"""Round-trip tests on a disposable native PostgreSQL 18 cluster.

Install the backend requirements, set the PG* connection options to a test
cluster, and set KT_BACKUP_TEST=1. The test creates and drops its own databases.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

import backup

RAW_NOTE = "  Ghi chú tiếng Việt 🗂️  \r\n<Dòng thứ hai>\n "
FIRST = datetime.fromisoformat("2026-11-18T17:20:31.123456+07:00")
LATER = FIRST + timedelta(minutes=3)
UTC_FIRST = "2026-11-18T10:20:31.123456+00:00"
DRIVE_ID = "synthetic-drive-file"
OAUTH_MARKER = "synthetic-oauth-fixture"
OPAQUE_MARKER = "opaque-fixture"


def new_database(register_cleanup):
    name = f"kt008_test_{uuid4().hex}"
    subprocess.run(
        ["createdb", "--no-password", "--maintenance-db=postgres",
         "--template=template0", "--encoding=UTF8", name],
        check=True, timeout=30,
    )
    register_cleanup(
        subprocess.run,
        ["dropdb", "--no-password", "--maintenance-db=postgres", name],
        check=True, timeout=30,
    )
    return name


def seed_database():
    from catalog.models import (
        Item, ItemProject, ItemTag, ItemTopic, Project, RelatedItem, Source, Tag, Topic,
    )
    from django.contrib.auth import get_user_model
    from django.contrib.sessions.models import Session
    from ingestion.models import CaptureEvent
    from jobs.models import Job
    from processing.models import DerivedContent
    from storage.models import Asset, DriveAccount, KnowledgeExport, StorageLocation

    owner = get_user_model().objects.create_user("kt008-fixture")
    note = Item.objects.create(owner=owner, kind="text", saved_at=FIRST, note=RAW_NOTE)
    link = Item.objects.create(owner=owner, kind="link", title="Tài liệu", saved_at=FIRST)
    original = "https://example.invalid/nguon?view=1"
    event = CaptureEvent.objects.create(
        owner=owner, item=note, raw_kind="text", raw_text=RAW_NOTE,
        server_received_at=FIRST, client_sent_at=FIRST - timedelta(seconds=1),
        idempotency_key="note-request",
    )
    CaptureEvent.objects.create(
        owner=owner, item=link, raw_kind="link", original_url=original,
        server_received_at=FIRST, idempotency_key="url-request",
    )
    CaptureEvent.objects.create(
        owner=owner, item=link, raw_kind="link", original_url=original + "&sent=again",
        server_received_at=LATER, idempotency_key="new-url-request",
    )
    Source.objects.create(
        item=link, original_url=original, canonical_url="https://example.invalid/nguon",
        identity_hash="b" * 64, captured_at=FIRST, metadata={"extra": OPAQUE_MARKER},
    )
    root = Topic.objects.create(owner=owner, name="Thư viện")
    topic = Topic.objects.create(owner=owner, name="Chủ đề", parent=root)
    project = Project.objects.create(owner=owner, name="Dự án")
    tag = Tag.objects.create(owner=owner, name="Ký hiệu")
    ItemTopic.objects.create(item=link, topic=topic, user_pinned=True)
    ItemProject.objects.create(item=link, project=project, user_pinned=True)
    ItemTag.objects.create(
        item=link, tag=tag, origin="auto", confidence=0.9,
        method_version="fixture-v1", source_version="1",
    )
    item_a, item_b = sorted((note.pk, link.pk))
    RelatedItem.objects.create(
        item_a_id=item_a, item_b_id=item_b, reason="Cùng nội dung nguồn",
        confidence=0.7, method_version="fixture-v1", source_version="1",
    )
    asset = Asset.objects.create(
        item=link, original_filename="Tài liệu.pdf", mime="application/pdf",
        size=17, sha256="a" * 64,
    )
    StorageLocation.objects.create(
        asset=asset, provider_file_id=DRIVE_ID, status="verified",
        verified_at=FIRST, provider_modified_at=FIRST, provider_revision="5",
    )
    DerivedContent.objects.create(
        item=link, asset=asset, kind="pdf_text", text="Văn bản có dấu.\n",
        source_locator={"page": 1}, processor="fixture", processor_version="1",
        input_hash=asset.sha256,
    )
    job = Job.objects.create(
        item=link, kind="fixture", idempotency_key="job-once", retry_at=LATER,
        input_ref={"extra": OPAQUE_MARKER},
    )
    DriveAccount.objects.create(
        owner=owner, google_user_id="synthetic-google-user",
        refresh_token_ciphertext=OAUTH_MARKER, state="connected",
    )
    Session.objects.create(session_key="synthetic-session", session_data="fixture", expire_date=LATER)
    KnowledgeExport.objects.create(item=link, provider_file_id="synthetic-knowledge-file", source_version="b" * 64, exported_version="b" * 64, status="disabled")
    return SimpleNamespace(note=note, link=link, event=event, asset=asset, job=job)


def cli(*args):
    return subprocess.run(
        [sys.executable, str(Path(backup.__file__)), *map(str, args)],
        capture_output=True, text=True, encoding="utf-8", timeout=45,
    )


@unittest.skipUnless(os.getenv("KT_BACKUP_TEST") == "1", "Set KT_BACKUP_TEST=1 for PostgreSQL tests.")
class BackupRoundTripTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.getenv("PGHOST") or not os.getenv("PGUSER"):
            raise RuntimeError("Set PGHOST and PGUSER to the disposable PostgreSQL test cluster.")
        cls.source = new_database(cls.addClassCleanup)
        cls.target = new_database(cls.addClassCleanup)
        cls.enterClassContext(patch.dict(os.environ, {
            "PGDATABASE": cls.source,
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "DJANGO_SECRET_KEY": "synthetic-kt008-django-test-key",
            "POSTGRES_DB": cls.source,
            "POSTGRES_USER": os.environ["PGUSER"],
            "POSTGRES_PASSWORD": os.getenv("PGPASSWORD", ""),
            "POSTGRES_HOST": os.environ["PGHOST"],
            "POSTGRES_PORT": os.getenv("PGPORT", "5432"),
            "GOOGLE_DRIVE_CLIENT_ID": "",
            "GOOGLE_DRIVE_CLIENT_SECRET": "",
            "GOOGLE_DRIVE_TOKEN_KEY": "",
        }))
        sys.path.insert(0, str(backup.ROOT / "apps" / "backend"))
        cls.addClassCleanup(sys.path.pop, 0)
        import django
        from django.core.management import call_command
        from django.db import connections

        django.setup()
        cls.addClassCleanup(connections.close_all)
        connections.databases["restored"] = {**connections.databases["default"], "NAME": cls.target}
        call_command("migrate", interactive=False, verbosity=0)
        cls.fixture = seed_database()

    def setUp(self):
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def assert_cli_ok(self, *args):
        result = cli(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_round_trip_via_local_copy_and_drive_mapping(self):
        from catalog.models import ItemTopic, Source
        from django.contrib.sessions.models import Session
        from django.db import IntegrityError, transaction
        from ingestion.models import CaptureEvent
        from storage.models import Asset, DriveAccount, KnowledgeExport
        from storage.service import DriveStorage

        package = self.directory / "backup"
        copy = self.directory / "independent-copy"
        self.assert_cli_ok("create", package)
        shutil.copytree(package, copy)
        self.assert_cli_ok("verify", copy)

        manifest = (copy / backup.MANIFEST).read_text(encoding="utf-8")
        self.assertNotIn(OAUTH_MARKER, manifest)
        self.assertNotIn(OPAQUE_MARKER, manifest)
        self.assertNotIn("synthetic-session", manifest)
        collections = backup.verify_bundle(copy)
        self.assertEqual(
            {name: len(rows) for name, rows in collections.items()},
            {"items": 2, "capture_events": 3, "sources": 1, "topics": 2, "projects": 1,
             "tags": 1, "item_topics": 1, "item_projects": 1, "item_tags": 1, "assets": 1,
             "storage_locations": 1, "derived_contents": 1, "related_items": 1, "jobs": 1, "knowledge_exports": 1},
        )
        event = next(row for row in collections["capture_events"] if row["id"] == str(self.fixture.event.pk))
        self.assertEqual(event["raw_text"], RAW_NOTE)
        self.assertEqual(event["server_received_at"], UTC_FIRST)
        self.assertEqual(collections["storage_locations"][0]["provider_file_id"], DRIVE_ID)
        self.assertEqual(collections['knowledge_exports'][0]['provider_file_id'], 'synthetic-knowledge-file')

        self.assert_cli_ok("restore", copy, "--target-db", self.target)
        self.assertFalse(DriveAccount.objects.using("restored").exists())
        self.assertFalse(Session.objects.using("restored").exists())
        self.assertEqual(KnowledgeExport.objects.using('restored').get().provider_file_id, 'synthetic-knowledge-file')
        self.assertEqual(Source.objects.using("restored").get().metadata, {"extra": OPAQUE_MARKER})
        assignment = ItemTopic.objects.using("restored").select_related("topic__parent").get()
        self.assertEqual(assignment.topic.parent.name, "Thư viện")
        self.assertTrue(assignment.user_pinned)

        restored_events = CaptureEvent.objects.using("restored")
        restored_note = restored_events.get(pk=self.fixture.event.pk)
        self.assertEqual(restored_note.item_id, self.fixture.note.pk)
        self.assertEqual(restored_note.raw_text, RAW_NOTE)
        self.assertEqual(restored_note.server_received_at, FIRST)
        self.assertEqual(restored_note.client_sent_at, FIRST - timedelta(seconds=1))
        self.assertEqual(
            list(restored_events.filter(item_id=self.fixture.link.pk)
                 .order_by("server_received_at").values_list("server_received_at", flat=True)),
            [FIRST, LATER],
        )
        with self.assertRaises(IntegrityError), transaction.atomic(using="restored"):
            restored_events.filter(pk=restored_note.pk).update(raw_text="changed")

        asset = Asset.objects.using("restored").select_related("item").get(pk=self.fixture.asset.pk)
        client = Mock()
        client.get_file.return_value = {
            "id": DRIVE_ID, "size": "17", "mimeType": asset.mime, "sha256Checksum": asset.sha256,
            "appProperties": {"kt_item_id": str(asset.item_id), "kt_asset_id": str(asset.pk)},
        }
        account = SimpleNamespace(owner_id=asset.item.owner_id)
        self.assertEqual(DriveStorage(client, account).open(asset), f"https://drive.google.com/open?id={DRIVE_ID}")
        self.assertEqual(client.get_file.call_args.args[0], DRIVE_ID)

        populated = cli("restore", package, "--target-db", self.target)
        self.assertEqual(populated.returncode, 1)
        self.assertIn("empty database", populated.stderr)

    def test_checksums_reject_damage_to_either_file(self):
        original = self.directory / "backup"
        self.assert_cli_ok("create", original)
        existing = cli("create", original)
        self.assertEqual(existing.returncode, 1)
        self.assertIn("new output directory", existing.stderr)
        self.assert_cli_ok("verify", original)
        for filename in (backup.DUMP, backup.MANIFEST):
            with self.subTest(filename=filename):
                copy = self.directory / filename
                shutil.copytree(original, copy)
                with (copy / filename).open("ab") as stream:
                    stream.write(b"\n")
                rejected = cli("verify", copy)
                self.assertEqual(rejected.returncode, 1)
                self.assertIn("checksum mismatch", rejected.stderr)

    def test_dump_and_manifest_share_snapshot_across_committed_write(self):
        from jobs.models import Job

        pg = backup.Postgres(compose=False)
        run = pg.run
        jobs = Job.objects.filter(pk=self.fixture.job.pk)

        def write_after_snapshot(tool, *args, **kwargs):
            if tool == "pg_dump" and "--format=custom" in args:
                jobs.update(state="done")
            return run(tool, *args, **kwargs)

        package = self.directory / "backup"
        self.addCleanup(jobs.update, state="queued")
        with patch.object(pg, "run", side_effect=write_after_snapshot):
            backup.create(pg, package)
        self.assertEqual(jobs.get().state, "done")
        self.assertEqual(backup.verify_bundle(package)["jobs"][0]["state"], "queued")
        target = new_database(self.addCleanup)
        self.assert_cli_ok("restore", package, "--target-db", target)


if __name__ == "__main__":
    unittest.main()
