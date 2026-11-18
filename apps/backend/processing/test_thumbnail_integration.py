import hashlib
import tempfile
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from catalog.models import Item
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import path
from django.utils import timezone
from jobs.models import Job
from ninja import NinjaAPI
from PIL import Image
from storage.drive import DriveError
from storage.models import Asset, StorageLocation
from storage.upload_job import UPLOAD_KIND, upload_asset

from .thumbnail_api import router
from .thumbnail_integration import rebuild_thumbnail, thumbnail_service

api = NinjaAPI(urls_namespace="thumbnail_integration_test")
api.add_router("", router)
urlpatterns = [path("api/v1/", api.urls)]


@override_settings(ROOT_URLCONF=__name__)
class ThumbnailIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create(username="owner")
        cls.other = get_user_model().objects.create(username="other")
        cls.item = Item.objects.create(owner=cls.owner, kind=Item.Kind.FILE)
        with Image.new("RGB", (6, 8), "red") as image, BytesIO() as file:
            image.save(file, format="PNG")
            cls.source = file.getvalue()
        cls.asset = Asset.objects.create(
            item=cls.item,
            mime="image/png",
            original_filename="source-image.png",
            size=len(cls.source),
            sha256=hashlib.sha256(cls.source).hexdigest(),
        )
        cls.location = StorageLocation.objects.create(
            asset=cls.asset,
            provider_file_id="mapped-file",
            status=StorageLocation.Status.VERIFIED,
            verified_at=timezone.now(),
        )
        cls.job = Job.objects.create(
            item=cls.item,
            kind=UPLOAD_KIND,
            idempotency_key=str(cls.asset.pk),
            input_ref={"asset_id": str(cls.asset.pk)},
        )

    def setUp(self):
        self.temp = self.enterContext(tempfile.TemporaryDirectory())
        self.upload_root = Path(self.temp) / "staging"
        self.upload_root.mkdir()
        self.enterContext(
            override_settings(
                THUMBNAIL_CACHE_DIR=Path(self.temp) / "thumbnails",
                UPLOAD_STAGING_ROOT=self.upload_root,
            )
        )
        self.staged = self.upload_root / self.asset.pk.hex
        self.url = f"/api/v1/assets/{self.asset.pk}/thumbnail"

    def test_api_requires_authenticated_owner_verified_location_and_cached_preview(
        self,
    ):
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.client.force_login(self.owner)
        miss = self.client.get(self.url)
        self.assertEqual(miss.status_code, 404)
        self.assertEqual(miss["Cache-Control"], "private, no-store")

        self.staged.write_bytes(self.source)
        upload_asset(self.job)
        self.assertFalse(self.staged.exists())
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/webp")
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertTrue(b"".join(response.streaming_content).startswith(b"RIFF"))

        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.client.force_login(self.owner)
        StorageLocation.objects.filter(pk=self.location.pk).update(
            status=StorageLocation.Status.INACCESSIBLE
        )
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_rendering_occurs_only_after_live_upload_verified_staging(self):
        self.staged.write_bytes(self.source)
        self.location.status = StorageLocation.Status.PENDING
        self.location.save(update_fields=["status"])

        def save(asset, file):
            self.assertEqual(file.read(), self.source)
            self.assertTrue(self.staged.exists())
            self.assertIsNone(
                thumbnail_service().get_cached(self.asset.pk, self.asset.sha256)
            )
            self.location.status = StorageLocation.Status.VERIFIED
            self.location.save(update_fields=["status"])
            return self.location

        with patch(
            "storage.upload_job.storage_for_owner",
            return_value=SimpleNamespace(save=save),
        ):
            upload_asset(self.job)
        self.assertFalse(self.staged.exists())
        self.assertIsNotNone(
            thumbnail_service().get_cached(self.asset.pk, self.asset.sha256)
        )

    def test_renderer_error_does_not_fail_or_retain_verified_source_upload(self):
        self.staged.write_bytes(self.source)
        with patch("processing.thumbnail_integration._generate", side_effect=OSError):
            upload_asset(self.job)
        self.assertFalse(self.staged.exists())
        self.location.refresh_from_db()
        self.assertEqual(self.location.status, StorageLocation.Status.VERIFIED)

    def drive_client(self):
        client = Mock()
        client.call.side_effect = lambda callback: callback()
        client.get_file.return_value = {
            "id": "mapped-file",
            "size": str(self.asset.size),
            "mimeType": self.asset.mime,
            "sha256Checksum": self.asset.sha256,
            "appProperties": {
                "kt_item_id": str(self.item.pk),
                "kt_asset_id": str(self.asset.pk),
            },
        }
        return client

    def fake_download(self, content):
        def make(sink, request, chunksize):
            def next_chunk():
                sink.write(content)
                return None, True

            return SimpleNamespace(next_chunk=next_chunk)

        return make

    def test_cache_rebuild_uses_authorized_mapping_and_verifies_bytes(self):
        client = self.drive_client()
        account = SimpleNamespace(owner_id=self.owner.pk)
        with (
            patch(
                "processing.thumbnail_integration.client_for_owner",
                return_value=(client, account),
            ),
            patch(
                "processing.thumbnail_integration.MediaIoBaseDownload",
                side_effect=self.fake_download(self.source),
            ),
        ):
            result = rebuild_thumbnail(self.asset.pk, owner_id=self.owner.pk)
            client.api.files.return_value.get_media.assert_called_once_with(
                fileId="mapped-file"
            )
            self.assertEqual(result.content_type, "image/webp")
            self.assertTrue(result.path.is_file())

    def test_rebuild_rejects_an_oversize_or_wrong_hash_download(self):
        client = self.drive_client()
        account = SimpleNamespace(owner_id=self.owner.pk)
        with patch(
            "processing.thumbnail_integration.client_for_owner",
            return_value=(client, account),
        ):
            for response, expected_error in [
                (self.source + b"1", "thumbnail_source_size_mismatch"),
                (b"x" + self.source[1:], "thumbnail_source_checksum_mismatch"),
            ]:
                with (
                    self.subTest(expected_error=expected_error),
                    patch(
                        "processing.thumbnail_integration.MediaIoBaseDownload",
                        side_effect=self.fake_download(response),
                    ),
                    self.assertRaisesRegex(DriveError, expected_error),
                ):
                    rebuild_thumbnail(self.asset.pk, owner_id=self.owner.pk)
        self.assertIsNone(
            thumbnail_service().get_cached(self.asset.pk, self.asset.sha256)
        )
