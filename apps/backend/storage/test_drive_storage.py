from hashlib import md5, sha256
from http import HTTPStatus
from io import BytesIO
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase

from catalog.models import Item

from .drive import DriveError
from .models import Asset, StorageLocation
from .service import DriveStorage


class FakeDrive:
    def __init__(self):
        self.files = {}
        self.reservations = 0
        self.uploads = 0
        self.lose_upload_response = False

    def reserve_file_id(self):
        self.reservations += 1
        return f"file-{self.reservations}"

    def get_file(self, file_id, fields):
        if file_id not in self.files:
            raise DriveError("drive_not_found", status=HTTPStatus.NOT_FOUND)
        return self.files[file_id]

    def upload_blob(self, stream, mime, metadata, *, resumable):
        self.uploads += 1
        if metadata["id"] in self.files:
            raise DriveError("drive_conflict", status=HTTPStatus.CONFLICT)
        data = stream.read()
        self.files[metadata["id"]] = {
            "id": metadata["id"],
            "size": str(len(data)),
            "mimeType": mime,
            "sha256Checksum": sha256(data).hexdigest(),
            "md5Checksum": md5(data, usedforsecurity=False).hexdigest(),
            "appProperties": metadata["appProperties"],
            "version": "1",
        }
        if self.lose_upload_response:
            raise DriveError("drive_unavailable", retryable=True)


class DriveStorageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create(username="owner")
        cls.item = Item.objects.create(owner=cls.owner, kind=Item.Kind.FILE)
        cls.payload = "nội dung gốc".encode()
        cls.asset = Asset.objects.create(
            item=cls.item,
            mime="text/plain",
            size=len(cls.payload),
            sha256=sha256(cls.payload).hexdigest(),
            original_filename="ghi-chu.txt",
        )

    def setUp(self):
        self.drive = FakeDrive()
        self.storage = DriveStorage(
            self.drive, SimpleNamespace(owner_id=self.owner.pk, root_folder_id="root")
        )

    def test_save_verify_stat_and_open(self):
        saved = self.storage.save(self.asset, BytesIO(self.payload))
        self.assertEqual(saved.status, StorageLocation.Status.VERIFIED)
        self.assertIsNotNone(saved.verified_at)
        self.assertEqual(self.storage.stat(self.asset).sha256, self.asset.sha256)
        self.assertEqual(
            self.storage.open(self.asset), "https://drive.google.com/open?id=file-1"
        )
        self.assertEqual(self.drive.reservations, 1)
        self.assertEqual(self.drive.uploads, 1)

    def test_timeout_after_remote_commit_reuses_file_id_and_does_not_duplicate(self):
        self.drive.lose_upload_response = True
        with self.assertRaisesRegex(DriveError, "^drive_unavailable$"):
            self.storage.save(self.asset, BytesIO(self.payload))
        location = self.asset.locations.get()
        self.assertEqual(location.status, StorageLocation.Status.PENDING)
        self.assertEqual(location.provider_file_id, "file-1")
        saved = self.storage.save(self.asset, BytesIO(self.payload))
        self.assertEqual(saved.status, StorageLocation.Status.VERIFIED)
        self.assertEqual(self.drive.reservations, 1)
        self.assertEqual(self.drive.uploads, 1)

    def test_altered_payload_or_remote_checksum_does_not_pass(self):
        with self.assertRaisesRegex(DriveError, "^storage_input_changed$"):
            self.storage.save(self.asset, BytesIO(b"tampered"))
        self.assertEqual(self.drive.reservations, 0)
        self.storage.save(self.asset, BytesIO(self.payload))
        self.drive.files["file-1"]["sha256Checksum"] = "tampered"
        with self.assertRaisesRegex(DriveError, "^storage_checksum_mismatch$"):
            self.storage.verify(self.asset)
        self.assertEqual(self.drive.uploads, 1)
