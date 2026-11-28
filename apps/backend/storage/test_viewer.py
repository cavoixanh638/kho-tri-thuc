"""Synthetic read-only source viewer API, provenance and transport tests."""

from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock, patch

from catalog.models import Item
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from .drive import DriveClient, DriveError
from .models import Asset, StorageLocation
from .service import DriveStorage, RemoteFile
from .viewer_api import MAX_RANGE, selected_range


class RangeSelectionTests(SimpleTestCase):
    def test_exact_suffix_open_ended_capped_and_invalid_ranges(self):
        self.assertEqual(selected_range("bytes=4-8", 10), (4, 8, True))
        self.assertEqual(selected_range("bytes=-4", 10), (6, 9, True))
        self.assertEqual(selected_range("bytes=4-", 10), (4, 9, True))
        self.assertEqual(selected_range("bytes=0-999", 10), (0, 9, True))
        self.assertEqual(selected_range(None, 10), (0, 9, False))
        self.assertEqual(
            selected_range("bytes=0-", MAX_RANGE * 2), (0, MAX_RANGE - 1, True)
        )
        for header in (
            "bytes=10-",
            "bytes=4-3",
            "bytes=-0",
            "bytes=-",
            "bytes=0-1,4-5",
            "items=0-1",
            "bytes=" + "9" * 21 + "-",
        ):
            with self.subTest(header=header), self.assertRaises(ValueError):
                selected_range(header, 10)
        with self.assertRaisesRegex(ValueError, "viewer_range_required"):
            selected_range(None, MAX_RANGE + 1)


class ViewerApiTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="viewer-owner")
        self.other = get_user_model().objects.create_user(username="viewer-other")
        self.item = Item.objects.create(
            owner=self.owner, kind="file", note="Giữ nguyên\r\n"
        )
        self.body = b"0123456789"
        self.asset = Asset.objects.create(
            item=self.item,
            original_filename="private.wav",
            size=len(self.body),
            sha256="a" * 64,
            mime="audio/wav",
            content_version=3,
        )
        self.location = StorageLocation.objects.create(
            asset=self.asset,
            provider_file_id="private-drive-id-never-expose",
            provider_revision="5",
            status="verified",
            verified_at=timezone.now(),
        )
        self.client.force_login(self.owner)
        self.descriptor = f"/api/v1/assets/{self.asset.pk}/viewer"
        self.url = f"/api/v1/assets/{self.asset.pk}/content/3/{self.asset.sha256}"
        self.factory = patch("storage.viewer_api.storage_for_owner")
        self.storage = self.factory.start().return_value
        self.addCleanup(self.factory.stop)
        self.storage.read_range.side_effect = lambda asset, start, end: self.body[
            start : end + 1
        ]

    def test_descriptor_probes_actual_range_and_pins_internal_id_hash_version(self):
        response = self.client.get(self.descriptor)
        self.assertEqual(response.status_code, 200)
        self.storage.read_range.assert_called_once()
        self.assertEqual(self.storage.read_range.call_args.args[1:], (0, 0))
        self.assertEqual(
            response.json(),
            {
                "assetId": str(self.asset.pk),
                "version": self.asset.sha256,
                "assetVersion": 3,
                "url": self.url,
                "kind": "media",
                "rangeVerified": True,
                "pageNavigationVerified": False,
            },
        )
        self.assertNotIn("private-drive-id", response.content.decode())
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["Cross-Origin-Resource-Policy"], "same-origin")

    def test_get_head_ranges_and_conditional_requests_are_consistent(self):
        full = self.client.get(self.url)
        self.assertEqual((full.status_code, full.content), (200, self.body))
        self.assertEqual(full["Accept-Ranges"], "bytes")
        for header, expected, content_range in (
            ("bytes=2-5", b"2345", "bytes 2-5/10"),
            ("bytes=7-", b"789", "bytes 7-9/10"),
            ("bytes=-2", b"89", "bytes 8-9/10"),
        ):
            with self.subTest(header=header):
                response = self.client.get(self.url, HTTP_RANGE=header)
                self.assertEqual(response.status_code, 206)
                self.assertEqual(response.content, expected)
                self.assertEqual(response["Content-Range"], content_range)
                self.assertEqual(response["Content-Length"], str(len(expected)))
        head = self.client.head(self.url)
        self.assertEqual(
            (head.status_code, head.content, head["Content-Length"]), (200, b"", "10")
        )
        head_range = self.client.head(self.url, HTTP_RANGE="bytes=2-5")
        self.assertEqual(
            (head_range.status_code, head_range.content, head_range["Content-Length"]),
            (206, b"", "4"),
        )
        self.assertEqual(
            self.client.get(
                self.url, HTTP_RANGE="bytes=2-5", HTTP_IF_RANGE=full["ETag"]
            ).status_code,
            206,
        )
        self.storage.read_range.reset_mock()
        for headers in ({"HTTP_IF_RANGE": '"old"'}, {"HTTP_IF_MATCH": '"old"'}):
            self.assertEqual(self.client.get(self.url, **headers).status_code, 412)
        self.storage.read_range.assert_not_called()

    def test_invalid_ranges_do_not_fetch_media(self):
        for header in ("bytes=10-", "bytes=9-8", "bytes=-0", "bytes=0-1,4-5"):
            response = self.client.get(self.url, HTTP_RANGE=header)
            self.assertEqual(response.status_code, 416)
            self.assertEqual(response["Content-Range"], "bytes */10")
        self.storage.read_range.assert_not_called()

    def test_owner_auth_deleted_stale_and_unverified_do_not_fetch_media(self):
        self.client.force_login(self.other)
        for url in (self.url, self.descriptor):
            self.assertEqual(self.client.get(url).status_code, 404)
        self.client.logout()
        for url in (self.url, self.descriptor):
            self.assertEqual(self.client.get(url).status_code, 401)
        self.client.force_login(self.owner)
        self.assertEqual(
            self.client.get(self.url.replace("/content/3/", "/content/2/")).status_code,
            409,
        )
        self.asset.content_version += 1
        self.asset.save()
        self.assertEqual(self.client.get(self.url).status_code, 409)
        self.location.status = "inaccessible"
        self.location.save()
        self.assertEqual(self.client.get(self.descriptor).status_code, 409)
        self.item.deleted_at = timezone.now()
        self.item.save()
        for url in (self.url, self.descriptor):
            self.assertEqual(self.client.get(url).status_code, 404)
        self.storage.read_range.assert_not_called()

    def test_large_source_requires_ranges_and_reads_at_most_one_slice(self):
        self.asset.size = MAX_RANGE * 2
        self.asset.save()
        self.assertEqual(self.client.get(self.url).status_code, 416)
        self.storage.read_range.assert_not_called()
        self.storage.read_range.side_effect = lambda asset, start, end: (
            b"x" * (end - start + 1)
        )
        response = self.client.get(self.url, HTTP_RANGE="bytes=0-")
        self.assertEqual(response.status_code, 206)
        self.assertEqual(len(response.content), MAX_RANGE)
        self.assertEqual(
            response["Content-Range"], f"bytes 0-{MAX_RANGE - 1}/{MAX_RANGE * 2}"
        )
        self.storage.read_range.reset_mock()
        head = self.client.head(self.url)
        self.assertEqual(
            (head.status_code, head["Content-Length"]), (200, str(MAX_RANGE * 2))
        )
        self.assertEqual(self.storage.read_range.call_args.args[1:], (0, 0))

    def test_storage_failures_and_unsupported_pdf_navigation_are_honest(self):
        self.storage.read_range.side_effect = DriveError(
            "sensitive-provider-id", retryable=True
        )
        response = self.client.get(self.descriptor)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("sensitive-provider-id", response.content.decode())
        self.storage.read_range.side_effect = None
        self.asset.mime = "application/pdf"
        self.asset.save()
        response = self.client.get(self.descriptor)
        self.assertFalse(response.json()["pageNavigationVerified"])
        self.asset.mime = "text/html"
        self.asset.save()
        self.assertEqual(self.client.get(self.descriptor).status_code, 409)
        self.item.refresh_from_db()
        self.assertEqual(self.item.note, "Giữ nguyên\r\n")
        self.assertEqual(self.item.user_edit_version, 0)


class DriveRangeProvenanceTests(TestCase):
    def setUp(self):
        owner = get_user_model().objects.create_user(username="range-owner")
        self.item = Item.objects.create(owner=owner, kind="file")
        self.asset = Asset.objects.create(
            item=self.item,
            mime="video/webm",
            size=10,
            sha256="a" * 64,
            original_filename="f.webm",
        )
        self.location = StorageLocation.objects.create(
            asset=self.asset,
            provider_file_id="private",
            provider_revision="7",
            status="verified",
            verified_at=timezone.now(),
        )
        self.client = Mock()
        self.storage = DriveStorage(self.client, SimpleNamespace(owner_id=owner.pk))
        self.remote = RemoteFile("private", 10, "video/webm", None, "7", "a" * 64, "")

    def test_reads_bounded_slice_without_mutating_location(self):
        self.client.read_blob_range.return_value = b"234"
        with patch.object(self.storage, "_read", return_value=self.remote):
            self.assertEqual(self.storage.read_range(self.asset, 2, 4), b"234")
        self.client.read_blob_range.assert_called_once_with("private", 2, 4, 10)
        self.location.refresh_from_db()
        self.assertEqual(self.location.provider_revision, "7")

    def test_changed_hash_revision_size_and_mid_read_changes_fail_closed(self):
        for changed in (
            replace(self.remote, sha256="b" * 64),
            replace(self.remote, revision="8"),
            replace(self.remote, size=11),
            replace(self.remote, sha256=""),
        ):
            with (
                self.subTest(changed=changed),
                patch.object(self.storage, "_read", return_value=changed),
                self.assertRaisesRegex(DriveError, "viewer_source_changed"),
            ):
                self.storage.read_range(self.asset, 2, 4)
        self.client.read_blob_range.assert_not_called()
        self.client.read_blob_range.return_value = b"234"
        with (
            patch.object(
                self.storage,
                "_read",
                side_effect=[self.remote, replace(self.remote, revision="8")],
            ),
            self.assertRaisesRegex(DriveError, "viewer_source_changed"),
        ):
            self.storage.read_range(self.asset, 2, 4)

    def test_metadata_version_can_advance_only_around_a_stable_binary_head(self):
        before = replace(self.remote, revision="8", head_revision_id="binary-A")
        after = replace(before, revision="9")
        self.client.read_blob_range.return_value = b"234"
        with patch.object(self.storage, "_read", side_effect=[before, after]):
            self.assertEqual(self.storage.read_range(self.asset, 2, 4), b"234")
        for unsafe in (replace(after, head_revision_id="binary-B"),
                       replace(after, sha256="b" * 64),
                       replace(after, revision="6"),
                       replace(after, head_revision_id="")):
            with self.subTest(unsafe=unsafe), patch.object(self.storage, "_read", side_effect=[before, unsafe]):
                with self.assertRaisesRegex(DriveError, "viewer_source_changed"):
                    self.storage.read_range(self.asset, 2, 4)


class DriveRangeTransportTests(SimpleTestCase):
    def make_client(self):
        client = DriveClient.__new__(DriveClient)
        client.api = Mock()
        client.api.files.return_value.get_media.return_value.uri = (
            "https://www.googleapis.com/drive/v3/files/fixture?alt=media"
        )
        client.credentials = Mock()
        client.on_reauthorize = Mock()
        return client

    def response(self, status=206, headers=None, chunks=(b"234",)):
        response = Mock()
        response.status_code = status
        response.headers = {
            "Content-Range": "bytes 2-4/10",
            "Content-Length": "3",
            **(headers or {}),
        }
        response.iter_content.return_value = iter(chunks)
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        return response

    def test_real_adapter_requests_only_google_range_no_redirect_and_closes_response(
        self,
    ):
        client, response = self.make_client(), self.response()
        with patch("storage.drive.requests.get", return_value=response) as get:
            self.assertEqual(client.read_blob_range("fixture", 2, 4, 10), b"234")
        self.assertFalse(get.call_args.kwargs["allow_redirects"])
        self.assertTrue(get.call_args.kwargs["stream"])
        self.assertEqual(get.call_args.kwargs["headers"]["Range"], "bytes=2-4")
        response.__exit__.assert_called_once()

    def test_ignore_range_redirect_oversize_encoding_and_wrong_range_rejected_before_read(
        self,
    ):
        client = self.make_client()
        for response in (
            self.response(status=200),
            self.response(status=302),
            self.response(headers={"Content-Length": "999999999"}),
            self.response(headers={"Content-Encoding": "gzip"}),
            self.response(headers={"Content-Range": "bytes 1-3/10"}),
        ):
            with (
                patch("storage.drive.requests.get", return_value=response),
                self.assertRaises(DriveError),
            ):
                client.read_blob_range("fixture", 2, 4, 10)
            response.iter_content.assert_not_called()
            response.__exit__.assert_called_once()

    def test_short_or_oversized_body_unavailable_source_and_expired_auth_fail_closed(
        self,
    ):
        client = self.make_client()
        for response in (
            self.response(chunks=(b"23",)),
            self.response(chunks=(b"2345",)),
            self.response(status=403),
            self.response(status=404),
            self.response(status=401),
        ):
            with (
                patch("storage.drive.requests.get", return_value=response),
                self.assertRaises(DriveError),
            ):
                client.read_blob_range("fixture", 2, 4, 10)
        client.on_reauthorize.assert_called_once()

    def test_oversized_request_and_untrusted_transport_target_never_connect(self):
        client = self.make_client()
        with patch("storage.drive.requests.get") as get:
            with self.assertRaises(DriveError):
                client.read_blob_range("fixture", 0, MAX_RANGE, MAX_RANGE + 1)
            client.api.files.return_value.get_media.return_value.uri = (
                "https://evil.invalid/source"
            )
            with self.assertRaises(DriveError):
                client.read_blob_range("fixture", 2, 4, 10)
            get.assert_not_called()
