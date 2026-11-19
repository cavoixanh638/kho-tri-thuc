import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import backup
import drive_bundle
import live_recovery


class Request:
    def __init__(self, action):
        self.action = action

    def execute(self):
        return self.action()


class FakeFiles:
    def __init__(self, client):
        self.client = client

    def list(self, **kwargs):
        return Request(lambda: {"files": []})

    def create(self, *, body, fields):
        def create():
            self.client.files[body["id"]] = body
            return body

        return Request(create)


class FakeDrive:
    def __init__(self):
        self.files = {}
        self.reservations = 0
        self.uploads = 0
        self.lose_upload_response = False
        self.api = self

    def reserve_file_id(self):
        self.reservations += 1
        return f"fake-{self.reservations}"

    def get_file(self, file_id, fields):
        from storage.drive import DriveError

        if file_id not in self.files:
            raise DriveError("drive_not_found", status=404)
        return self.files[file_id]

    def execute(self, request):
        return request.execute()

    def files(self):
        return FakeFiles(self)

    def upload_blob(self, stream, mime, metadata, *, resumable):
        from storage.drive import DriveError

        data = stream.read()
        self.uploads += 1
        self.files[metadata["id"]] = {
            **metadata,
            "size": str(len(data)),
            "mimeType": mime,
            "sha256Checksum": hashlib.sha256(data).hexdigest(),
            "md5Checksum": hashlib.md5(data, usedforsecurity=False).hexdigest(),
        }
        if self.lose_upload_response:
            self.lose_upload_response = False
            raise DriveError("drive_unavailable", retryable=True)
        return {"id": metadata["id"]}


class DriveBundleTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.bundle = self.root / "bundle"
        self.bundle.mkdir()
        (self.bundle / backup.DUMP).write_bytes(b"fake-pg-dump-for-container-tests")
        (self.bundle / backup.MANIFEST).write_text(
            json.dumps(
                {
                    "schema_version": backup.SCHEMA_VERSION,
                    "postgres_major": backup.PG_MAJOR,
                    "collections": {name: [] for name in backup.COLLECTIONS},
                }
            ),
            encoding="utf-8",
        )
        (self.bundle / backup.CHECKSUMS).write_text(
            backup.checksum_lines(self.bundle), encoding="ascii"
        )
        self.archive = self.root / "backup.zip"

    def test_v1_manifest_remains_readable_without_knowledge_collection(self):
        manifest = json.loads((self.bundle / backup.MANIFEST).read_text(encoding="utf-8"))
        manifest['schema_version'] = 1
        del manifest['collections']['knowledge_exports']
        (self.bundle / backup.MANIFEST).write_text(json.dumps(manifest), encoding='utf-8')
        (self.bundle / backup.CHECKSUMS).write_text(backup.checksum_lines(self.bundle), encoding='ascii')
        rows = backup.verify_bundle(self.bundle)
        self.assertEqual(len(rows), 14)
        self.assertNotIn(b'storage_knowledgeexport', backup.manifest_query(rows))

    def test_deterministic_pack_and_verified_unpack(self):
        first = drive_bundle.pack(self.bundle, self.archive)
        second = self.root / "second.zip"
        self.assertEqual(drive_bundle.pack(self.bundle, second), first)
        restored = self.root / "restored"
        drive_bundle.unpack(self.archive, restored)
        self.assertEqual(
            backup.verify_bundle(restored), backup.verify_bundle(self.bundle)
        )
        with self.assertRaises(backup.BackupError):
            drive_bundle.unpack(self.archive, restored)

    def test_archive_rejects_extra_traversal_entry(self):
        drive_bundle.pack(self.bundle, self.archive)
        with zipfile.ZipFile(self.archive, "a") as archive:
            archive.writestr("../outside", b"bad")
        with self.assertRaisesRegex(backup.BackupError, "Unexpected files"):
            drive_bundle.unpack(self.archive, self.root / "restored")
        self.assertFalse((self.root / "outside").exists())

    def test_upload_retry_after_lost_response_reuses_reserved_id(self):
        from storage.drive import DriveError

        drive_bundle.pack(self.bundle, self.archive)
        drive = FakeDrive()
        state = self.root / "state"
        # Fake API keeps files() callable separately from its in-memory dictionary.
        drive.api = type("API", (), {"files": lambda _self: FakeFiles(drive)})()
        copies = drive_bundle.DriveBackups(drive, "fake-root", state)
        drive.lose_upload_response = True
        with self.assertRaises(DriveError):
            copies.upload(self.archive)
        restarted = drive_bundle.DriveBackups(drive, "fake-root", state)
        file_id = restarted.upload(self.archive)
        self.assertEqual(restarted.upload(self.archive), file_id)
        self.assertEqual(drive.uploads, 1)
        self.assertEqual(drive.reservations, 2)
        self.assertEqual(len(drive.files), 2)

    def test_changed_remote_bytes_are_not_replaced_or_marked_verified(self):
        drive_bundle.pack(self.bundle, self.archive)
        drive = FakeDrive()
        drive.api = type("API", (), {"files": lambda _self: FakeFiles(drive)})()
        copies = drive_bundle.DriveBackups(drive, "fake-root", self.root / "state")
        file_id = copies.upload(self.archive)
        drive.files[file_id]["sha256Checksum"] = "0" * 64
        with self.assertRaisesRegex(backup.BackupError, "checksum mismatch"):
            copies.upload(self.archive)
        self.assertEqual(drive.uploads, 1)

    def test_download_checksum_failure_cleans_only_pending_file(self):
        data = b"backup bytes"

        class Download:
            def __init__(self, sink, request, chunksize):
                self.sink = sink

            def next_chunk(self):
                self.sink.write(data)
                return None, True

        class Client:
            api = type(
                "API",
                (),
                {
                    "files": lambda _self: type(
                        "Files",
                        (),
                        {
                            "get_media": lambda _self, **kwargs: object(),
                        },
                    )()
                },
            )()

            def call(self, action):
                return action()

        target = self.root / "download.zip"
        with (
            patch("drive_bundle.MediaIoBaseDownload", Download),
            self.assertRaisesRegex(backup.BackupError, "checksum mismatch"),
        ):
            drive_bundle.download(Client(), "fake-id", target, len(data), "0" * 64)
        self.assertFalse(target.exists())
        self.assertFalse(target.with_suffix(".pending").exists())

    def test_auditor_rejects_non_disposable_database_before_reading_runtime(self):
        work = self.root / "audit-must-not-exist"
        args = SimpleNamespace(target_db="production", work_dir=work)
        with self.assertRaisesRegex(backup.BackupError, "kt_recovery_"):
            live_recovery.audit(args, {})
        self.assertFalse(work.exists())

    def test_source_environment_forces_read_only_connections(self):
        configured = live_recovery._native_pg(
            {
                "environment": {
                    "POSTGRES_HOST": "127.0.0.1",
                    "POSTGRES_PORT": "54329",
                    "POSTGRES_USER": "synthetic-owner",
                    "POSTGRES_PASSWORD": "synthetic-secret",
                    "POSTGRES_DB": "synthetic-source",
                }
            }
        )
        self.assertEqual(configured["PGOPTIONS"], "-c default_transaction_read_only=on")
        self.assertEqual(configured["PGDATABASE"], "synthetic-source")


if __name__ == "__main__":
    unittest.main()
