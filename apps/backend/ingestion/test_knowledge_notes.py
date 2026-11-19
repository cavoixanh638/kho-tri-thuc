import tempfile
from io import StringIO
from pathlib import Path

from catalog.models import Item
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TransactionTestCase
from storage.models import Asset, KnowledgeExport

from .models import CaptureEvent


class KnowledgeNoteImportTests(TransactionTestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="knowledge-import-owner"
        )
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "article.md"
        self.body = (
            "# Tri thức tiếng Việt\r\n\r\n**Nội dung chính**, giữ nguyên dấu.\r\n"
        )
        self.path.write_bytes(self.body.encode())

    def run_import(self, **kwargs):
        call_command(
            "import_knowledge_notes",
            str(self.path),
            owner=self.owner.username,
            stdout=StringIO(),
            **kwargs,
        )

    def test_preview_is_read_only_and_import_is_idempotent_without_overwriting_user_edits(
        self,
    ):
        self.run_import()
        self.assertFalse(Item.objects.exists())
        self.run_import(apply=True, export=True)
        item = Item.objects.get()
        self.assertEqual(item.note, self.body)
        self.assertEqual(item.title, "Tri thức tiếng Việt")
        self.assertEqual(CaptureEvent.objects.get().raw_text, self.body)
        self.assertFalse(Asset.objects.exists())
        self.assertTrue(KnowledgeExport.objects.get(item=item).enabled)
        item.note = "Nội dung người dùng đã chỉnh"
        item.save(update_fields=["note"])
        self.run_import(apply=True, export=True)
        item.refresh_from_db()
        self.assertEqual(item.note, "Nội dung người dùng đã chỉnh")
        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(CaptureEvent.objects.count(), 1)
        self.assertEqual(CaptureEvent.objects.get().raw_text, self.body)

    def test_changed_import_body_is_refused_instead_of_overwriting_original_capture(
        self,
    ):
        self.run_import(apply=True)
        self.path.write_text("# Bài đã thay đổi\nNội dung mới", encoding="utf-8")
        with self.assertRaises(CommandError):
            self.run_import(apply=True)
        self.assertEqual(Item.objects.get().note, self.body)
        self.assertEqual(CaptureEvent.objects.get().raw_text, self.body)
