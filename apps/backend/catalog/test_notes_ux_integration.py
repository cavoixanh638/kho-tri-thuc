"""Joint HTTP contracts across capture, authored notes, review and backlinks.

Synthetic PostgreSQL data only. No Drive, AI provider or external worker call.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from ingestion.models import CaptureEvent
from processing.knowledge import snapshot
from storage.models import Asset

from .models import Item, ItemTopic, Topic


@override_settings(SUGGESTION_REVIEW_POC_ENABLED=True)
class NotesUxIntegrationTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="ux-joint")
        self.client.force_login(self.owner)

    def post(self, path, body, **headers):
        return self.client.post(
            "/api/v1" + path, body, content_type="application/json", headers=headers
        )

    def patch(self, item, body):
        return self.client.patch(
            f"/api/v1/items/{item.pk}", body, content_type="application/json"
        )

    def test_capture_template_review_undo_backlink_export_keep_one_identity(self):
        raw = "# Tri thức Tiếng Việt\r\nGiữ nguyên văn và giờ nhận.  \r\n"
        submitted = self.post(
            "/captures", {"kind": "text", "text": raw}, **{"Idempotency-Key": "joint"}
        )
        self.assertEqual(submitted.status_code, 201, submitted.content)
        receipt = submitted.json()
        replay = self.post(
            "/captures", {"kind": "text", "text": raw}, **{"Idempotency-Key": "joint"}
        )
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.json(), receipt)
        item = Item.objects.get(pk=receipt["item_id"])
        event = CaptureEvent.objects.values().get(pk=receipt["capture_id"])
        topic = Topic.objects.create(owner=self.owner, name="Kho / Lĩnh vực")
        ItemTopic.objects.create(item=item, topic=topic, user_pinned=True, origin="user")
        # An attachment is distinct from the note; pending is deliberately not Drive PASS.
        asset = Asset.objects.create(
            item=item, original_filename="synthetic.pdf", mime="application/pdf",
            size=12, sha256="a" * 64,
        )
        asset_before = Asset.objects.values().get(pk=asset.pk)
        groups_before = list(ItemTopic.objects.values())
        peer = Item.objects.create(owner=self.owner, kind="text", note="Bài tham khảo")
        edited = raw + f"\r\n# Bài học\r\n\r\n## Ý chính\r\n[Đối chiếu](#/muc/{peer.pk})\r\n"
        saved = self.patch(item, {"note": edited, "expected_edit_version": 0})
        self.assertEqual(saved.status_code, 200, saved.content)
        self.assertEqual(saved.json()["item_id"], receipt["item_id"])
        self.assertEqual(saved.json()["user_edit_version"], 1)
        self.assertEqual(
            self.patch(item, {"note": "Stale", "expected_edit_version": 0}).status_code,
            409,
        )
        path = f"/items/{item.pk}/suggestions/"
        proposed = edited + "\r\n> Đề xuất thủ công cần duyệt.\r\n"
        preview = self.post(path + "preview", {"proposed_note": proposed}).json()
        self.assertEqual(preview["before"].encode(), edited.encode())
        self.assertEqual(preview["base_edit_version"], 1)
        self.assertEqual(preview["provenance"]["provider"], "none")
        self.assertEqual(Item.objects.get(pk=item.pk).note, edited)
        accepted = self.post(path + "accept", {"receipt": preview["receipt"]})
        self.assertEqual(accepted.status_code, 200, accepted.content)
        self.assertEqual(accepted.json()["edit_version"], 2)
        # An editor opened before review cannot overwrite the accepted proposal.
        self.assertEqual(
            self.patch(item, {"note": edited, "expected_edit_version": 1}).status_code,
            409,
        )
        undone = self.post(
            path + "undo", {"receipt": accepted.json()["undo_receipt"]}
        )
        self.assertEqual(undone.status_code, 200, undone.content)
        self.assertEqual(undone.json()["edit_version"], 3)
        self.assertEqual(Item.objects.get(pk=item.pk).note.encode(), edited.encode())
        knowledge = self.client.get(f"/api/v1/items/{item.pk}/knowledge").json()
        self.assertEqual(knowledge["text"].encode(), edited.encode())
        backlinks = self.client.get(f"/api/v1/items/{peer.pk}/related").json()
        self.assertEqual([hit["item_id"] for hit in backlinks["backlinks"]], [str(item.pk)])
        for format in ("markdown", "text"):
            exported = snapshot(item.pk, format)
            self.assertFalse(exported.blocked)
            self.assertIn(str(item.pk).encode(), exported.body)
            self.assertIn("Đối chiếu".encode(), exported.body)
        self.assertEqual(CaptureEvent.objects.count(), 1)
        self.assertEqual(CaptureEvent.objects.values().get(pk=receipt["capture_id"]), event)
        self.assertEqual(Asset.objects.values().get(pk=asset.pk), asset_before)
        self.assertEqual(list(ItemTopic.objects.values()), groups_before)
        self.assertEqual(Item.objects.count(), 2)

    def test_manual_save_after_accept_blocks_undo_without_losing_later_edit(self):
        item = Item.objects.create(owner=self.owner, kind="text", note="Gốc")
        path = f"/items/{item.pk}/suggestions/"
        proposal = self.post(path + "preview", {"proposed_note": "Đề xuất"}).json()
        accepted = self.post(path + "accept", {"receipt": proposal["receipt"]}).json()
        later = "Người dùng biên soạn tiếp Tiếng Việt\r\n"
        self.assertEqual(
            self.patch(item, {"note": later, "expected_edit_version": 1}).status_code,
            200,
        )
        undo = self.post(path + "undo", {"receipt": accepted["undo_receipt"]})
        self.assertEqual(undo.status_code, 409)
        item.refresh_from_db()
        self.assertEqual(item.note.encode(), later.encode())
        self.assertEqual(item.user_edit_version, 2)
