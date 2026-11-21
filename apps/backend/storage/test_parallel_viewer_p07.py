"""P07 isolated HTTP Range and PDF/MP4 viewer acceptance, synthetic storage only.

Run in a disposable PostgreSQL QA database:
  python manage.py test storage.test_parallel_viewer_p07
No Google Drive credentials, production assets, or permanent storage needed.
"""

from unittest.mock import patch

from catalog.models import Item
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from .drive import DriveError
from .models import Asset, StorageLocation
from .viewer_api import MAX_RANGE, selected_range


class P07RangeContractTests(SimpleTestCase):
    def test_closed_open_ended_and_suffix(self):
        self.assertEqual(selected_range("bytes=3-8", 10), (3, 8, True))
        self.assertEqual(selected_range("bytes=7-", 10), (7, 9, True))
        self.assertEqual(selected_range("bytes=-6", 10), (4, 9, True))
        self.assertEqual(selected_range("bytes=-100", 10), (0, 9, True))
        self.assertEqual(selected_range("bytes=0-100", 10), (0, 9, True))
        self.assertEqual(selected_range(None, 10), (0, 9, False))
        self.assertEqual(
            selected_range("bytes=1-", MAX_RANGE * 25),
            (1, MAX_RANGE, True),
        )

    def test_100_mib_source_suffix_6_mib_is_not_silently_truncated(self):
        size = 100 * 1024 * 1024
        with self.assertRaisesRegex(ValueError, "^viewer_range_too_large$"):
            selected_range("bytes=-6291456", size)
        with self.assertRaisesRegex(ValueError, "^viewer_range_too_large$"):
            selected_range("bytes=0-6291455", size)
        self.assertEqual(
            selected_range(f"bytes=-{MAX_RANGE}", size),
            (size - MAX_RANGE, size - 1, True),
        )

    def test_invalid_unsatisfiable_and_multi_range(self):
        for header in (
            "bytes=-", "bytes=-0", "bytes=100-99", "bytes=0-1,2-3",
            "items=0-1", "BYTES=0-1", "bytes=999999999-",
            "bytes=" + "9" * 21 + "-",
        ):
            with self.subTest(header=header), self.assertRaises(ValueError):
                selected_range(header, 100)
        with self.assertRaisesRegex(ValueError, "^viewer_range_required$"):
            selected_range(None, MAX_RANGE + 1)


class P07ViewerApiTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="p07-owner")
        self.other = get_user_model().objects.create_user(username="p07-other")
        self.item = Item.objects.create(owner=self.owner, kind="file", note="original")
        self.asset = Asset.objects.create(
            item=self.item,
            mime="application/pdf",
            original_filename="private.pdf",
            size=100 * 1024 * 1024,
            sha256="a" * 64,
            content_version=7,
        )
        self.location = StorageLocation.objects.create(
            asset=self.asset,
            provider_file_id="SECRET-drive-id",
            provider_revision="11",
            status=StorageLocation.Status.VERIFIED,
            verified_at=timezone.now(),
        )
        self.descriptor = f"/api/v1/assets/{self.asset.pk}/viewer"
        self.url = f"/api/v1/assets/{self.asset.pk}/content/7/{self.asset.sha256}"
        self.client.force_login(self.owner)
        factory = patch("storage.viewer_api.storage_for_owner")
        self.storage = factory.start().return_value
        self.addCleanup(factory.stop)
        self.reads = []

        def read_range(asset, start, end):
            self.reads.append((start, end))
            return b"P" * (end - start + 1)

        self.storage.read_range.side_effect = read_range

    def test_pdf_descriptor_and_range_headers_never_expose_drive_id(self):
        descriptor = self.client.get(self.descriptor)
        self.assertEqual(descriptor.status_code, 200)
        self.assertEqual(descriptor.json()["kind"], "pdf")
        self.assertFalse(descriptor.json()["pageNavigationVerified"])
        self.assertEqual(self.reads, [(0, 0)])
        self.assertNotIn(b"SECRET-drive-id", descriptor.content)
        self.reads.clear()
        response = self.client.get(self.url, HTTP_RANGE="bytes=10-13")
        self.assertEqual(response.status_code, 206)
        self.assertEqual(response.content, b"PPPP")
        self.assertEqual(response["Content-Range"], f"bytes 10-13/{self.asset.size}")
        self.assertEqual(response["Content-Length"], "4")
        self.assertEqual(response["Accept-Ranges"], "bytes")
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["Cross-Origin-Resource-Policy"], "same-origin")
        self.assertEqual(response["Vary"], "Cookie")
        self.assertNotIn("Access-Control-Allow-Origin", response)
        self.assertNotIn(b"SECRET-drive-id", response.content)
        self.assertEqual(self.reads, [(10, 13)])

    def test_100_mib_suffix_and_closed_oversize_return_416_without_drive_read(self):
        for header in ("bytes=-6291456", "bytes=0-6291455",
                       "bytes=-0", "bytes=999999999-", "bytes=0-3,6-9"):
            with self.subTest(header=header):
                response = self.client.get(self.url, HTTP_RANGE=header)
                self.assertEqual(response.status_code, 416)
                self.assertEqual(response["Content-Range"], f"bytes */{self.asset.size}")
                self.assertEqual(response["Accept-Ranges"], "bytes")
                self.assertIn("ETag", response)
        self.storage.read_range.assert_not_called()

    def test_100_mib_suffix_4_mib_and_open_ended_are_exact(self):
        last = self.client.get(self.url, HTTP_RANGE=f"bytes=-{MAX_RANGE}")
        self.assertEqual(last.status_code, 206)
        self.assertEqual(last["Content-Length"], str(MAX_RANGE))
        self.assertEqual(
            last["Content-Range"],
            f"bytes {self.asset.size - MAX_RANGE}-{self.asset.size - 1}/{self.asset.size}",
        )
        self.assertEqual(len(last.content), MAX_RANGE)
        opened = self.client.get(self.url, HTTP_RANGE="bytes=100-")
        self.assertEqual(opened.status_code, 206)
        self.assertEqual(opened["Content-Range"], f"bytes 100-{100 + MAX_RANGE - 1}/{self.asset.size}")
        self.assertEqual(self.reads, [
            (self.asset.size - MAX_RANGE, self.asset.size - 1),
            (100, 100 + MAX_RANGE - 1),
        ])

    def test_mp4_twenty_seeks_and_head_consistency(self):
        self.asset.mime = "video/mp4"
        self.asset.save(update_fields=["mime"])
        size = self.asset.size
        head = self.client.head(self.url)
        self.assertEqual((head.status_code, head["Content-Length"]), (200, str(size)))
        self.assertEqual(head.content, b"")
        self.assertEqual(self.reads, [(0, 0)])
        self.reads.clear()
        for n in range(20):
            start = n * (size // 20)
            result = self.client.get(self.url, HTTP_RANGE=f"bytes={start}-{start + 511}")
            self.assertEqual(result.status_code, 206)
            self.assertEqual(result.content, b"P" * 512)
            self.assertEqual(result["Content-Range"], f"bytes {start}-{start + 511}/{size}")
        self.assertEqual(len(self.reads), 20)
        self.assertTrue(all(end - start + 1 == 512 for start, end in self.reads))

    def test_version_etag_auth_soft_delete_and_wrong_owner_fail_before_read(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.client.force_login(self.owner)
        for headers in (
            {"HTTP_IF_RANGE": '"stale"'},
            {"HTTP_IF_MATCH": '"stale"'},
        ):
            self.assertEqual(
                self.client.get(self.url, HTTP_RANGE="bytes=0-3", **headers).status_code,
                412,
            )
        self.assertEqual(
            self.client.get(self.url.replace("/content/7/", "/content/6/")).status_code,
            409,
        )
        self.location.status = StorageLocation.Status.INACCESSIBLE
        self.location.save(update_fields=["status"])
        self.assertEqual(self.client.get(self.url, HTTP_RANGE="bytes=0-3").status_code, 409)
        self.item.deleted_at = timezone.now()
        self.item.save(update_fields=["deleted_at"])
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.storage.read_range.assert_not_called()

    def test_adapter_short_or_overlong_payload_returns_502_not_false_206(self):
        self.storage.read_range.return_value = b""
        self.storage.read_range.side_effect = None
        self.assertEqual(self.client.get(self.url, HTTP_RANGE="bytes=0-3").status_code, 502)
        self.storage.read_range.return_value = b"12345"
        self.assertEqual(self.client.get(self.url, HTTP_RANGE="bytes=0-3").status_code, 502)
        self.storage.read_range.side_effect = DriveError("sensitive", retryable=True)
        bad = self.client.get(self.url, HTTP_RANGE="bytes=0-3")
        self.assertEqual(bad.status_code, 503)
        self.assertNotIn("sensitive", bad.content.decode())
        self.assertEqual(self.item.note, "original")
