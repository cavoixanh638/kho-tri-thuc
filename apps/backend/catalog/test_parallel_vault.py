"""P02 / KT127: synthetic PostgreSQL roundtrip and adversarial ZIP cases."""

import io
import json
import zipfile
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from ingestion.models import CaptureEvent
from storage.models import Asset

from .models import Item, ItemTopic, Source, Topic
from .vault import (
    MANIFEST, VaultError, apply_import, digest, export_vault,
    parse_vault, preview_import,
)


def edit_zip(data, replacements):
    result = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(data)) as reader, zipfile.ZipFile(result, "w") as writer:
        existing = set()
        for entry in reader.infolist():
            existing.add(entry.filename)
            raw = replacements.get(entry.filename, reader.read(entry))
            writer.writestr(entry.filename, raw)
        for name, raw in replacements.items():
            if name not in existing:
                writer.writestr(name, raw)
    return result.getvalue()


class ParallelVaultTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = get_user_model()
        cls.owner = user.objects.create_user(username="p02-owner")
        cls.other = user.objects.create_user(username="p02-other")

    def seed(self, items=4, topics=5, media=2, links=False):
        groups = []
        for i in range(topics):
            groups.append(Topic.objects.create(
                owner=self.owner, name="Nhánh Tiếng Việt " + str(i),
                parent=groups[-1] if i % 5 else None,
                sort_order=i,
            ))
        created = []
        for i in range(items):
            item = Item.objects.create(
                owner=self.owner, kind="text", title="Ghi chú Tiếng Việt " + str(i),
                note="Nguyên văn Tiếng Việt\r\n", home_topic=groups[i % topics],
                parent_item=created[-1] if i % 10 else None,
                outline_order=i,
            )
            ItemTopic.objects.create(item=item, topic=groups[i % topics], user_pinned=True)
            if i == 0:
                for t in groups[1:3]:
                    ItemTopic.objects.create(item=item, topic=t, user_pinned=True)
            CaptureEvent.objects.create(
                owner=self.owner, item=item, raw_kind="text", raw_text=item.note,
            )
            if i < media:
                Asset.objects.create(
                    item=item, mime="video/mp4", sha256=("%064x" % (i + 1)),
                    size=110 * 1024 * 1024 * 1024,
                    original_filename="video-%s.mp4" % i,
                )
            created.append(item)
        if links:
            for i, item in enumerate(created):
                target = created[(i+1) % items]
                item.note += "[Theo dõi](#/muc/" + str(target.pk) + ")\n"
                item.note += "[Liên kết](#/muc/" + str(created[(i+2) % items].pk) + ")\n"
                item.save(update_fields=["note"])
        return created

    def test_exact_portable_100_items_30_folders_200_links_5_media_and_retry(self):
        articles = self.seed(items=100, topics=30, media=5, links=True)
        original = {
            str(item.pk): (item.note, item.saved_at, item.parent_item_id, item.home_topic_id)
            for item in articles
        }
        archived = export_vault(self.owner)
        data, archive_sha = parse_vault(archived)
        self.assertEqual(archive_sha, digest(archived))
        self.assertEqual(
            (len(data["items"]), len(data["topics"]), len(data["item_topics"]),
             len(data["events"]), len(data["assets"])),
            (100, 30, 102, 100, 5),
        )
        self.assertEqual(sum(row["_note"].count("](#/muc/") for row in data["items"]), 200)
        self.assertLess(len(archived), 2 * 1024 * 1024)
        self.assertEqual(len({row["path"] for row in data["items"]}), 100)
        self.assertNotIn(b"provider_file_id", archived)
        self.assertNotIn(b"refresh_token", archived)

        # Simulate a fresh library while retaining the same owner: the import
        # must recreate UUIDs, saved_at, hierarchy, membership and history.
        CaptureEvent.objects.filter(owner=self.owner).delete()
        Asset.objects.filter(item__owner=self.owner).delete()
        ItemTopic.objects.filter(item__owner=self.owner).delete()
        Item.objects.filter(owner=self.owner).delete()
        Topic.objects.filter(owner=self.owner).delete()
        preview = preview_import(self.owner, archived)
        self.assertEqual(preview["counts"]["new"], 100)
        receipt = preview["receipt"]
        done = apply_import(self.owner, archived, receipt, ["*"])
        self.assertEqual(done["created"], 100)
        self.assertEqual(done["events_created"], 100)
        self.assertEqual(done["assets_created"], 5)
        self.assertEqual(done["media_verified"], 0)
        self.assertEqual(ItemTopic.objects.count(), 102)
        self.assertEqual(CaptureEvent.objects.count(), 100)
        self.assertEqual(Asset.objects.count(), 5)
        for item in Item.objects.filter(owner=self.owner):
            note, saved, parent_id, home_id = original[str(item.pk)]
            self.assertEqual(item.note, note)
            self.assertEqual(item.saved_at, saved)
            self.assertEqual(item.parent_item_id, parent_id)
            self.assertIsNotNone(home_id)
            self.assertIsNotNone(item.home_topic_id)
        replay = apply_import(self.owner, archived, receipt, ["*"])
        self.assertEqual(replay["state"], "unchanged")
        self.assertEqual(CaptureEvent.objects.count(), 100)
        self.assertEqual(Asset.objects.count(), 5)

    def test_selective_import_only_creates_selected_note_folder_closure(self):
        folder_a = Topic.objects.create(owner=self.owner, name="P02-Folder A")
        folder_b = Topic.objects.create(owner=self.owner, name="P02-Folder B")
        note_a = Item.objects.create(
            owner=self.owner, kind="text", title="P02-Note A",
            note="Nội dung A", home_topic=folder_a,
        )
        note_b = Item.objects.create(
            owner=self.owner, kind="text", title="P02-Note B",
            note="Nội dung B", home_topic=folder_b,
        )
        ItemTopic.objects.create(item=note_a, topic=folder_a, user_pinned=True)
        ItemTopic.objects.create(item=note_b, topic=folder_b, user_pinned=True)
        chosen_id = str(note_a.pk)
        other_id = str(note_b.pk)
        archive = export_vault(self.owner)
        ItemTopic.objects.filter(item__owner=self.owner).delete()
        Item.objects.filter(owner=self.owner).delete()
        Topic.objects.filter(owner=self.owner).delete()
        preview = preview_import(self.owner, archive)
        result = apply_import(self.owner, archive, preview["receipt"], [chosen_id])
        self.assertEqual(result["created"], 1)
        self.assertTrue(Item.objects.filter(owner=self.owner, pk=chosen_id).exists())
        self.assertFalse(Item.objects.filter(owner=self.owner, pk=other_id).exists())
        self.assertTrue(Topic.objects.filter(owner=self.owner, name="P02-Folder A").exists())
        self.assertFalse(Topic.objects.filter(owner=self.owner, name="P02-Folder B").exists())
        self.assertEqual(ItemTopic.objects.filter(item__owner=self.owner).count(), 1)

    def test_owner_conflicts_never_expose_foreign_note(self):
        item = Item.objects.create(owner=self.owner, kind="text", title="Riêng")
        archive = export_vault(self.owner)
        Item.objects.filter(pk=item.pk).update(owner=self.other)
        output = preview_import(self.owner, archive)
        self.assertEqual(output["counts"]["conflict"], 1)
        self.assertIsNone(output["rows"][0]["before"])
        with self.assertRaisesRegex(VaultError, "vault_import_conflict"):
            apply_import(self.owner, archive, output["receipt"], ["*"])
        self.assertEqual(Item.objects.get(pk=item.pk).owner_id, self.other.pk)

    def test_newer_local_version_cannot_be_overwritten(self):
        item = self.seed(items=1, topics=1, media=0)[0]
        archive = export_vault(self.owner)
        Item.objects.filter(pk=item.pk).update(note="Dữ liệu mới", user_edit_version=9)
        output = preview_import(self.owner, archive)
        self.assertEqual(output["counts"]["conflict"], 1)
        with self.assertRaises(VaultError):
            apply_import(self.owner, archive, output["receipt"], ["*"])
        self.assertEqual(Item.objects.get(pk=item.pk).note, "Dữ liệu mới")

    def test_preview_receipt_rejects_stale_revision_and_wrong_owner(self):
        item = self.seed(items=1, topics=1, media=0)[0]
        archive = export_vault(self.owner)
        receipt = preview_import(self.owner, archive)["receipt"]
        Item.objects.filter(pk=item.pk).update(note="Đổi ngay", user_edit_version=1)
        with self.assertRaisesRegex(VaultError, "vault_import_conflict"):
            apply_import(self.owner, archive, receipt, ["*"])
        with self.assertRaisesRegex(VaultError, "scope_mismatch"):
            apply_import(self.other, archive, receipt, ["*"])

    def test_rejects_path_traversal_unknown_version_and_tampered_metadata(self):
        self.seed(items=1, topics=1, media=0)
        archive = export_vault(self.owner)
        bad = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(archive)) as source, zipfile.ZipFile(bad, "w") as output:
            for info in source.infolist():
                output.writestr("../evil.md" if info.filename.endswith(".md") else info.filename, source.read(info))
        with self.assertRaisesRegex(VaultError, "unsafe_archive_path"):
            parse_vault(bad.getvalue())
        with zipfile.ZipFile(io.BytesIO(archive)) as reader:
            manifest = json.loads(reader.read(MANIFEST))
        manifest["schema_version"] = 99
        hostile = edit_zip(archive, {MANIFEST: json.dumps(manifest).encode()})
        with self.assertRaisesRegex(VaultError, "unsupported_vault_format"):
            parse_vault(hostile)
        manifest["schema_version"] = 1
        manifest["items"][0]["parent_item_id"] = str(uuid4())
        hostile = edit_zip(archive, {MANIFEST: json.dumps(manifest).encode()})
        with self.assertRaisesRegex(VaultError, "invalid_vault_hierarchy"):
            parse_vault(hostile)

    def test_zip_bomb_rejected_before_inflation(self):
        self.seed(items=1, topics=1, media=0)
        archive = export_vault(self.owner)
        giant = b"x" * (3 * 1024 * 1024)
        bomb = edit_zip(archive, {"Notes/bomb.md": giant})
        with self.assertRaisesRegex(VaultError, "zip_bomb_or_file_limit"):
            parse_vault(bomb)

    def test_foreign_asset_collision_rollback_atomic(self):
        self.seed(items=1, topics=1, media=1)
        archive = export_vault(self.owner)
        foreign = Item.objects.create(owner=self.other, kind="text", title="Foreign")
        with zipfile.ZipFile(io.BytesIO(archive)) as reader:
            manifest = json.loads(reader.read(MANIFEST))
        Asset.objects.filter(item__owner=self.owner).delete()
        foreign_asset = Asset.objects.create(
            item=foreign, mime="video/mp4", original_filename="external.mp4",
            sha256=manifest["assets"][0]["sha256"], size=1,
            id=manifest["assets"][0]["id"],
        )
        # Existing item is unchanged; force an author-edited Markdown update.
        item = Item.objects.get(owner=self.owner)
        Item.objects.filter(pk=item.pk).update(note="Mới", user_edit_version=0)
        preview = preview_import(self.owner, archive)
        with self.assertRaisesRegex(VaultError, "vault_asset_identity_conflict"):
            apply_import(self.owner, archive, preview["receipt"], ["*"])
        self.assertEqual(Item.objects.get(pk=item.pk).note, "Mới")
        self.assertEqual(Asset.objects.get(pk=foreign_asset.pk).item_id, foreign.pk)
