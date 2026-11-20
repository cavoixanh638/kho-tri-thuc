from catalog.models import Item
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from storage.models import Asset

from .models import DerivedContent
from .read_knowledge import MAX_TEXT, ReadKnowledgeService


class ReadKnowledgeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(
            username="read-knowledge-owner"
        )
        cls.other = get_user_model().objects.create_user(
            username="read-knowledge-other"
        )

    def part(self, item, text, **kwargs):
        return DerivedContent.objects.create(
            item=item,
            kind="web_text",
            text=text,
            processor="public-web",
            processor_version="1",
            input_hash="a" * 64,
            **kwargs,
        )

    def test_authored_markdown_remains_authoritative_when_source_text_is_available(
        self,
    ):
        item = Item.objects.create(
            owner=self.owner, kind="text", note="# Người dùng\nNội dung đã chốt.  "
        )
        self.part(item, "Không ghi đè bằng nguồn")
        result = ReadKnowledgeService().read(item)
        self.assertEqual(result["origin"], "authored")
        self.assertEqual(result["text"], item.note)
        self.assertEqual(result["parts"], [])
        self.assertFalse(result["needs_review"])
        item.refresh_from_db()
        self.assertEqual(item.note, "# Người dùng\nNội dung đã chốt.  ")

    def test_current_transcript_takes_precedence_over_web_metadata_and_stale_transcript(
        self,
    ):
        item = Item.objects.create(owner=self.owner, kind="link")
        media = Asset.objects.create(
            item=item, mime="video/mp4", original_filename="example.mp4"
        )
        self.part(item, "Mô tả trang web không phải lời nói")
        transcript = DerivedContent.objects.create(
            item=item,
            asset=media,
            kind="video_transcript",
            text="[00:01–00:04] Nội dung lời nói hiện hành",
            source_locator={"section": "00:01–00:04"},
            processor="faster-whisper",
            processor_version="base-v1",
            input_hash="b" * 64,
        )
        DerivedContent.objects.create(
            item=item,
            asset=media,
            kind="video_transcript",
            text="Bản cũ không được đọc",
            status="stale",
            processor="faster-whisper",
            processor_version="old",
            input_hash="c" * 64,
        )
        result = ReadKnowledgeService().read(item)
        self.assertEqual(result["origin"], "extracted")
        self.assertEqual([part["id"] for part in result["parts"]], [transcript.pk])
        self.assertTrue(result["needs_review"])
        self.assertEqual(result["parts"][0]["asset_id"], media.pk)
        self.assertEqual(result["parts"][0]["locator"], {"section": "00:01–00:04"})

    def test_read_api_owner_deleted_missing_and_truncation_states_are_explicit(self):
        item = Item.objects.create(owner=self.owner, kind="link")
        self.client.force_login(self.owner)
        url = f"/api/v1/items/{item.pk}/knowledge"
        missing = self.client.get(url)
        self.assertEqual(missing.status_code, 200)
        self.assertEqual(missing.json()["origin"], "missing")
        part = self.part(
            item, "x" * (MAX_TEXT + 10), source_locator={"section": "long"}
        )
        data = self.client.get(url).json()
        self.assertTrue(data["truncated"])
        self.assertEqual(len(data["parts"][0]["text"]), MAX_TEXT)
        self.assertEqual(data["parts"][0]["id"], part.pk)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.owner)
        item.deleted_at = timezone.now()
        item.save(update_fields=["deleted_at"])
        self.assertEqual(self.client.get(url).status_code, 404)
