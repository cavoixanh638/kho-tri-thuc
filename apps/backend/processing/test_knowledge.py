from catalog.models import Item, ItemTopic, Source, Topic
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from ingestion.models import CaptureEvent
from storage.models import Asset, KnowledgeExport

from .knowledge import MAX_CHARS, snapshot
from .models import DerivedContent


class KnowledgeSnapshotTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="snapshot-owner")
        self.other = get_user_model().objects.create_user(username="snapshot-other")
        self.item = Item.objects.create(
            owner=self.owner,
            kind="text",
            title="Tiếng Việt",
            note="  Ghi chú\nnguyên văn  ",
        )
        self.event = CaptureEvent.objects.create(
            owner=self.owner, item=self.item, raw_kind="text", raw_text=self.item.note
        )

    def part(self, **changes):
        return DerivedContent.objects.create(
            item=self.item,
            kind="pdf_text",
            text="Đoạn trích đúng trang",
            processor="fixture",
            processor_version="1",
            input_hash="a" * 64,
            source_locator={"page": 4},
            **changes,
        )

    def test_snapshot_is_deterministic_and_does_not_edit_user_input(self):
        original_times = self.item.saved_at, self.event.server_received_at
        first = snapshot(self.item.pk)
        self.assertEqual(first, snapshot(self.item.pk))
        self.assertIn(self.item.note, first.body.decode())
        self.item.refresh_from_db()
        self.event.refresh_from_db()
        self.assertEqual(
            (self.item.saved_at, self.event.server_received_at), original_times
        )
        self.assertEqual(self.event.raw_text, "  Ghi chú\nnguyên văn  ")
        self.assertFalse(KnowledgeExport.objects.exists())
        Item.objects.filter(pk=self.item.pk).update(note="Thay đổi ghi chú")
        self.assertNotEqual(first.version, snapshot(self.item.pk).version)

    def test_active_evidence_has_locator_and_stale_text_is_excluded(self):
        part = self.part()
        first = snapshot(self.item.pk)
        self.assertIn(b'"page": 4', first.body)
        part.status = "stale"
        part.save(update_fields=["status"])
        second = snapshot(self.item.pk)
        self.assertNotEqual(first.version, second.version)
        self.assertNotIn("Đoạn trích", second.body.decode())

    def test_group_names_are_scoped_to_item_owner(self):
        topic = Topic.objects.create(owner=self.owner, name="Nhóm của tôi")
        foreign = Topic.objects.create(
            owner=self.other, name="Nhóm riêng tài khoản khác"
        )
        ItemTopic.objects.create(item=self.item, topic=topic)
        ItemTopic.objects.create(item=self.item, topic=foreign)
        body = snapshot(self.item.pk).body.decode()
        self.assertIn(topic.name, body)
        self.assertNotIn(foreign.name, body)

    def test_video_metadata_or_empty_transcript_does_not_claim_spoken_content(self):
        Asset.objects.create(
            item=self.item, mime="video/mp4", original_filename="fixture.mp4"
        )
        part = self.part()
        part.kind = "transcript"
        part.text = ""
        part.save(update_fields=["kind", "text"])
        self.assertIn("CHƯA CÓ TRANSCRIPT VIDEO", snapshot(self.item.pk).body.decode())
        part.text = "Nội dung lời nói đã trích"
        part.save(update_fields=["text"])
        self.assertNotIn(
            "CHƯA CÓ TRANSCRIPT VIDEO", snapshot(self.item.pk).body.decode()
        )

    def test_long_content_is_explicitly_partial_and_tail_updates_change_version(self):
        part = self.part()
        part.text = "x" * (MAX_CHARS + 100) + "tail-one"
        part.save(update_fields=["text"])
        first = snapshot(self.item.pk)
        self.assertTrue(first.truncated)
        self.assertIn("BẢN XUẤT CÓ GIỚI HẠN", first.body.decode())
        part.text = "x" * (MAX_CHARS + 100) + "tail-two"
        part.save(update_fields=["text"])
        self.assertNotEqual(first.version, snapshot(self.item.pk).version)

    def test_sixty_thousand_character_note_is_exported_once_with_source_and_capture_provenance(
        self,
    ):
        note = "Nội dung tiếng Việt đã biên soạn. " * 1900
        self.assertGreater(len(note), 60_000)
        item = Item.objects.create(
            owner=self.owner, kind="text", title="Bài dài", note=note
        )
        capture = CaptureEvent.objects.create(
            owner=self.owner, item=item, raw_kind="text", raw_text=note
        )
        source_url = "https://example.com/reference-for-long-note"
        Source.objects.create(
            item=item,
            original_url=source_url,
            canonical_url=source_url,
            identity_hash="c" * 64,
        )
        Asset.objects.create(
            item=item,
            mime="application/pdf",
            original_filename="reference-document.pdf",
            sha256="d" * 64,
        )
        for format in ("markdown", "text"):
            with self.subTest(format=format):
                result = snapshot(item.pk, format)
                body = result.body.decode()
                self.assertFalse(result.truncated)
                self.assertEqual(body.count(note), 1)
                self.assertEqual(body.count("Ghi chú người dùng"), 1)
                self.assertEqual(body.count("Nội dung trích xuất hiện hành"), 1)
                self.assertIn(source_url, body)
                self.assertIn("reference-document.pdf", body)
                self.assertIn(str(capture.server_received_at), body)
                self.assertIn(
                    "Nội dung trùng với ghi chú người dùng hiện hành ở trên.", body
                )
                self.assertLess(body.index(note), body.index("Tệp gốc"))
        capture.refresh_from_db()
        self.assertEqual(capture.raw_text, note)

    def test_sixty_thousand_character_extraction_keeps_locator_once_before_media(self):
        self.item.note = ""
        self.item.save(update_fields=["note"])
        part = self.part()
        part.text = "Văn bản trích từ nguồn có dấu. " * 2100
        self.assertGreater(len(part.text), 60_000)
        part.save(update_fields=["text"])
        result = snapshot(self.item.pk)
        body = result.body.decode()
        self.assertFalse(result.truncated)
        self.assertEqual(body.count(part.text), 1)
        self.assertEqual(body.count("## Nội dung trích xuất hiện hành"), 1)
        self.assertIn('pdf_text — fixture 1 — {"page": 4}', body)
        self.assertLess(body.index(part.text), body.index("## Tệp gốc"))

    def test_credential_like_input_is_blocked_and_deleted_item_is_tombstone(self):
        Item.objects.filter(pk=self.item.pk).update(
            note="client_secret=" + "fixture" * 8
        )
        blocked = snapshot(self.item.pk)
        self.assertTrue(blocked.blocked)
        self.assertEqual(blocked.body, b"")
        Item.objects.filter(pk=self.item.pk).update(deleted_at=timezone.now())
        deleted = snapshot(self.item.pk)
        self.assertFalse(deleted.blocked)
        self.assertEqual(deleted.body, b"")
        self.assertNotEqual(deleted.version, blocked.version)
