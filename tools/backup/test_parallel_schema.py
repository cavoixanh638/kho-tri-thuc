"""P03 regression: v1-v5 wire formats, relationships and atomic rollback.

Run unit tests unconditionally; for real PG18 round-trips:
  KT_BACKUP_TEST=1 PGHOST=... PGUSER=... python -m unittest discover -s tools/backup -p 'test_parallel_schema*.py' -v
This creates and drops UUID-named disposable test databases only.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from uuid import uuid4

import backup


def make_bundle(root, version, collections=None):
    root.mkdir()
    (root / backup.DUMP).write_bytes(b"synthetic archive")
    payload = {
        "schema_version": version,
        "postgres_major": backup.PG_MAJOR,
        "created_at": "2026-11-21T00:00:00+00:00",
        "collections": collections if collections is not None
        else {name: [] for name in backup.collections_for_version(version)},
    }
    (root / backup.MANIFEST).write_text(json.dumps(payload) + "\n", encoding="utf-8")
    (root / backup.CHECKSUMS).write_text(backup.checksum_lines(root), encoding="ascii")
    return payload


class ParallelSchemaUnitTests(unittest.TestCase):
    def test_projection_is_append_only_and_old_versions_stable(self):
        old = backup.collections_for_version(3)
        self.assertEqual(len(old), 15)
        self.assertEqual(len(backup.collections_for_version(1)), 14)
        self.assertEqual(set(backup.collections_for_version(2)), set(old))
        self.assertEqual(backup.collections_for_version(3)["items"], backup.COLLECTIONS["items"])
        self.assertNotIn("home_topic_id", old["items"][1])
        for version in (1, 2):
            self.assertNotIn("node_kind", backup.collections_for_version(version)["topics"][1])
        current = backup.collections_for_version(4)
        self.assertEqual(len(current), 17)
        for field in ("home_topic_id", "parent_item_id", "outline_order",
                      "structure_version", "structure_origin"):
            self.assertIn(field, current["items"][1])
        self.assertIn("capture_id", current["clip_annotations"][1])
        self.assertIn("query", current["saved_collections"][1])
        self.assertEqual(current["capture_events"], old["capture_events"])
        self.assertEqual(current["assets"], old["assets"])
        self.assertNotIn("excluded_topics", current)
        self.assertEqual(set(backup.collections_for_version(5)), {*current, "excluded_topics"})

    def test_legacy_and_current_bundle_checksums(self):
        with tempfile.TemporaryDirectory() as directory:
            for version in backup.SUPPORTED_SCHEMA_VERSIONS:
                root = Path(directory) / str(version)
                expected = make_bundle(root, version)
                self.assertEqual(backup.verify_bundle(root), expected["collections"])
                tampered = json.loads((root / backup.MANIFEST).read_text())
                tampered["collections"]["items"].append({"id": "synthetic"})
                (root / backup.MANIFEST).write_text(json.dumps(tampered))
                with self.assertRaisesRegex(backup.BackupError, "checksum mismatch"):
                    backup.verify_bundle(root)

    def test_incompatible_versions_and_missing_or_extra_collections_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            for version in (0, 6):
                root = Path(directory) / str(version)
                root.mkdir()
                (root / backup.DUMP).write_bytes(b"data")
                (root / backup.MANIFEST).write_text(json.dumps({
                    "schema_version": version, "postgres_major": 18, "collections": {},
                }))
                (root / backup.CHECKSUMS).write_text(backup.checksum_lines(root))
                with self.assertRaises(backup.BackupError):
                    backup.verify_bundle(root)
            for change in ("removed", "extra"):
                root = Path(directory) / change
                payload = make_bundle(root, 4)
                if change == "removed":
                    payload["collections"].pop("clip_annotations")
                else:
                    payload["collections"]["unexpected"] = []
                (root / backup.MANIFEST).write_text(json.dumps(payload))
                (root / backup.CHECKSUMS).write_text(backup.checksum_lines(root))
                with self.assertRaisesRegex(backup.BackupError, "collections"):
                    backup.verify_bundle(root)

    def test_restore_assertion_embeds_utf8_as_hex_not_sql(self):
        payload = {"items": [{"note": "'); COMMIT; DROP TABLE confidential; --",
                              "unicode": "Tiếng Việt 🗂️", "id": str(uuid4())}]}
        with patch.object(backup, "manifest_select", return_value="SELECT '{}'::json"):
            sql = backup.restore_assertion_sql(payload, 4)
        self.assertTrue(sql.endswith(b"COMMIT;\n"))
        self.assertIn(b"RAISE EXCEPTION", sql)
        self.assertIn(b"convert_from(decode('", sql)
        self.assertNotIn(b"DROP TABLE confidential", sql)
        self.assertEqual(sql.count(b"COMMIT;"), 1)

    def test_legacy_projection_has_no_v4_table_reference(self):
        for v in (1, 2, 3):
            query = backup.manifest_query(schema_version=v).decode()
            self.assertNotIn("catalog_savedcollection", query)
            self.assertNotIn("processing_clipannotation", query)
            self.assertNotIn("home_topic_id", query)
            self.assertTrue(query.endswith("COMMIT;\n"))


@unittest.skipUnless(os.getenv("KT_BACKUP_TEST") == "1", "requires disposable PostgreSQL 18")
class ParallelSchemaPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from test_backup import new_database, seed_database
        if not os.getenv("PGHOST") or not os.getenv("PGUSER"):
            raise RuntimeError("Set PGHOST and PGUSER to an isolated PostgreSQL 18 cluster")
        cls.source = new_database(cls.addClassCleanup)
        cls.enterClassContext(patch.dict(os.environ, {
            "PGDATABASE": cls.source,
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "DJANGO_SECRET_KEY": "synthetic-p03-only",
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
        call_command("migrate", interactive=False, verbosity=0)
        cls.fixtures = seed_database()
        from catalog.models import Item, ItemTopicExclusion, Topic, SavedCollection
        from processing.models import ClipAnnotation
        note, link = cls.fixtures.note, cls.fixtures.link
        topic = Topic.objects.get(name="Chủ đề")
        cls.exclusion = ItemTopicExclusion.objects.create(item=link, topic=topic.parent)
        Item.objects.filter(pk=note.pk).update(home_topic=topic, outline_order=17,
                                               structure_version=3, structure_origin="user")
        Item.objects.filter(pk=link.pk).update(parent_item=note, outline_order=9,
                                               structure_version=4, structure_origin="user")
        cls.collection = SavedCollection.objects.create(
            owner=note.owner, name="Ghim của tôi", normalized_name="ghim cua toi",
            query={"all": [{"field": "favorite", "operator": "eq", "value": True}]},
            view="table", version=2,
        )
        cls.clip = ClipAnnotation.objects.create(
            item=note, capture=cls.fixtures.event, mode="quote",
            quote="Một câu quan trọng", quote_hash="a" * 64,
            locator={"page": 3, "fragment": "đoạn 2"}, source_url="https://example.invalid/clip",
            verification="verified", inserted_edit_version=5,
        )

    def setUp(self):
        from test_backup import new_database
        self.target = new_database(self.addCleanup)
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.bundle = self.directory / "source"
        backup.create(backup.Postgres(False), self.bundle)

    def test_full_restore_exact_uuids_timestamps_structure_and_exclusions(self):
        from catalog.models import Item, ItemTopicExclusion, SavedCollection
        from ingestion.models import CaptureEvent
        from processing.models import ClipAnnotation
        from django.db import connections
        from storage.models import Asset, DriveAccount
        expected = backup.verify_bundle(self.bundle)
        self.assertEqual(len(expected), 18)
        self.assertEqual(len(expected["excluded_topics"]), 1)
        self.assertEqual(len(expected["saved_collections"]), 1)
        self.assertEqual(len(expected["clip_annotations"]), 1)
        self.assertEqual(expected["clip_annotations"][0]["locator"],
                         {"page": 3, "fragment": "đoạn 2"})
        self.assertEqual(expected["items"][0].keys() >= {
            "home_topic_id", "parent_item_id", "structure_version", "outline_order",
        }, True)
        pg = backup.Postgres(False)
        pg.psql(f"""ALTER DATABASE "{self.target}" SET timezone TO 'Asia/Ho_Chi_Minh'""".encode())
        backup.restore(pg, self.bundle, self.target)
        alias = "p03_restored"
        connections.databases[alias] = {
            **connections.databases["default"], "NAME": self.target,
        }
        self.addCleanup(connections[alias].close)
        self.assertEqual(SavedCollection.objects.using(alias).get().pk, self.collection.pk)
        restored = ItemTopicExclusion.objects.using(alias).get()
        self.assertEqual((restored.item_id, restored.topic_id), (self.exclusion.item_id, self.exclusion.topic_id))
        self.assertEqual(ClipAnnotation.objects.using(alias).get().pk, self.clip.pk)
        self.assertEqual(ClipAnnotation.objects.using(alias).get().capture_id,
                         self.fixtures.event.pk)
        link = Item.objects.using(alias).get(pk=self.fixtures.link.pk)
        self.assertEqual(link.parent_item_id, self.fixtures.note.pk)
        self.assertEqual(link.outline_order, 9)
        note = Item.objects.using(alias).get(pk=self.fixtures.note.pk)
        self.assertEqual(note.structure_version, 3)
        event = CaptureEvent.objects.using(alias).get(pk=self.fixtures.event.pk)
        self.assertEqual(event.server_received_at, self.fixtures.event.server_received_at)
        self.assertEqual(event.raw_text, self.fixtures.event.raw_text)
        self.assertEqual(Asset.objects.using(alias).get().pk, self.fixtures.asset.pk)
        self.assertFalse(DriveAccount.objects.using(alias).exists())

    def test_mismatch_aborts_restore_and_leaves_target_empty(self):
        manifest = json.loads((self.bundle / backup.MANIFEST).read_text())
        manifest["collections"]["items"][0]["title"] = "injected mismatch"
        (self.bundle / backup.MANIFEST).write_text(json.dumps(manifest))
        (self.bundle / backup.CHECKSUMS).write_text(backup.checksum_lines(self.bundle))
        with self.assertRaises(backup.BackupError):
            backup.restore(backup.Postgres(False), self.bundle, self.target)
        self.assertEqual(backup.Postgres(False).psql(backup.EMPTY_DATABASE, self.target), b"t")

    def test_legacy_projections_against_new_schema(self):
        pg = backup.Postgres(False)
        for version in (1, 2, 3, 4):
            expected = json.loads(pg.psql(backup.TRANSACTION + backup.manifest_query(
                schema_version=version,
            ), self.source))
            self.assertEqual(set(expected), set(backup.collections_for_version(version)))
            self.assertNotIn("excluded_topics", expected)
            if version < 4:
                self.assertNotIn("home_topic_id", expected["items"][0])
                self.assertNotIn("clip_annotations", expected)


if __name__ == "__main__":
    unittest.main()
