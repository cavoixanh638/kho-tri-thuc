import json

from catalog.models import Item, ItemTopic, Topic
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from ingestion.models import CaptureEvent
from storage.models import Asset

from .models import DerivedContent


@override_settings(SUGGESTION_REVIEW_POC_ENABLED=True)
class SuggestionReviewTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="review-owner")
        self.other = get_user_model().objects.create_user(username="review-other")
        self.client.force_login(self.owner)

    def send(self, item, action, data):
        return self.client.post(
            f"/api/v1/items/{item.pk}/suggestions/{action}",
            json.dumps(data),
            content_type="application/json",
        )

    def article(self, index):
        before = f"# Bài tiếng Việt {index}\r\nĐ/đ nguyên văn e\u0302\u0301\r\n\n| A | B |\n|---|---|\n| {index} | Chữ |\n"
        item = Item.objects.create(
            owner=self.owner, kind="text", note=before, user_edit_version=index
        )
        event = CaptureEvent.objects.create(
            owner=self.owner, item=item, raw_kind="text", raw_text=before
        )
        asset = Asset.objects.create(
            item=item,
            mime="text/plain",
            size=12,
            sha256="a" * 64,
            original_filename="fixture.txt",
        )
        topic = Topic.objects.create(owner=self.owner, name=f"Nhóm {index}")
        ItemTopic.objects.create(item=item, topic=topic, user_pinned=True)
        return item, event, asset

    def test_twenty_previews_rejects_accepts_and_undo_keep_originals(self):
        for index in range(20):
            with self.subTest(index=index):
                item, event, asset = self.article(index)
                before = item.note
                event_before = CaptureEvent.objects.filter(pk=event.pk).values().get()
                asset_before = Asset.objects.filter(pk=asset.pk).values().get()
                group_before = list(ItemTopic.objects.filter(item=item).values())
                after = before + f"\n> Gợi ý tổng hợp {index}: cần người dùng duyệt.\n"
                response = self.send(item, "preview", {"proposed_note": after})
                self.assertEqual(response.status_code, 200, response.content)
                preview = response.json()
                self.assertEqual(preview["before"], before)
                self.assertEqual(preview["after"], after)
                self.assertEqual(preview["base_edit_version"], index)
                self.assertEqual(preview["provenance"]["provider"], "none")
                item.refresh_from_db()
                self.assertEqual(item.note, before)
                rejected = self.send(item, "reject", {"receipt": preview["receipt"]})
                self.assertEqual(rejected.json(), {"state": "rejected", "writes": 0})
                item.refresh_from_db()
                self.assertEqual(item.note, before)
                accepted = self.send(item, "accept", {"receipt": preview["receipt"]})
                self.assertEqual(accepted.status_code, 200, accepted.content)
                self.assertEqual(accepted.json()["note"], after)
                item.refresh_from_db()
                self.assertEqual(item.user_edit_version, index + 1)
                self.assertEqual(
                    self.send(
                        item, "accept", {"receipt": preview["receipt"]}
                    ).status_code,
                    409,
                )
                undone = self.send(
                    item, "undo", {"receipt": accepted.json()["undo_receipt"]}
                )
                self.assertEqual(undone.status_code, 200, undone.content)
                item.refresh_from_db()
                self.assertEqual(item.note.encode(), before.encode())
                self.assertEqual(item.user_edit_version, index + 2)
                self.assertEqual(
                    CaptureEvent.objects.filter(pk=event.pk).values().get(),
                    event_before,
                )
                self.assertEqual(
                    Asset.objects.filter(pk=asset.pk).values().get(), asset_before
                )
                self.assertEqual(
                    list(ItemTopic.objects.filter(item=item).values()), group_before
                )

    def test_manual_edit_and_source_version_conflicts_block_accept_and_undo(self):
        item, _, _ = self.article(0)
        token = self.send(item, "preview", {"proposed_note": "Đề xuất"}).json()[
            "receipt"
        ]
        item.note = "Người dùng đã sửa trước khi duyệt"
        item.user_edit_version += 1
        item.save()
        self.assertEqual(self.send(item, "accept", {"receipt": token}).status_code, 409)
        token = self.send(item, "preview", {"proposed_note": "Đề xuất mới"}).json()[
            "receipt"
        ]
        part = DerivedContent.objects.create(
            item=item,
            kind="web_text",
            text="Nguồn mới",
            processor="fixture",
            processor_version="v1",
            input_hash="b" * 64,
        )
        self.assertEqual(self.send(item, "accept", {"receipt": token}).status_code, 409)
        token = self.send(item, "preview", {"proposed_note": "Đề xuất mới"}).json()[
            "receipt"
        ]
        accepted = self.send(item, "accept", {"receipt": token}).json()
        part.text = "Nguồn đã đổi tiếp"
        part.save()
        self.assertEqual(
            self.send(item, "undo", {"receipt": accepted["undo_receipt"]}).status_code,
            409,
        )
        item.refresh_from_db()
        self.assertEqual(item.note, "Đề xuất mới")

    def test_receipt_scope_tampering_expiry_and_feature_gate(self):
        from unittest.mock import patch

        item, _, _ = self.article(0)
        token = self.send(item, "preview", {"proposed_note": "Đề xuất"}).json()[
            "receipt"
        ]
        self.assertEqual(
            self.send(item, "accept", {"receipt": token + "x"}).status_code, 422
        )
        self.client.force_login(self.other)
        self.assertEqual(self.send(item, "accept", {"receipt": token}).status_code, 422)
        self.assertEqual(
            self.send(item, "preview", {"proposed_note": "Trộm"}).status_code, 404
        )
        self.client.force_login(self.owner)
        with patch("django.core.signing.time.time", return_value=9_999_999_999):
            self.assertEqual(
                self.send(item, "accept", {"receipt": token}).status_code, 422
            )
        with override_settings(SUGGESTION_REVIEW_POC_ENABLED=False):
            self.assertEqual(
                self.send(item, "preview", {"proposed_note": "X"}).status_code, 404
            )
        self.client.logout()
        self.assertEqual(
            self.send(item, "preview", {"proposed_note": "X"}).status_code, 401
        )

    def test_invalid_text_and_csrf_cannot_write(self):
        item, _, _ = self.article(0)
        for note in ("a\0b", "x" * 100_001):
            self.assertEqual(
                self.send(item, "preview", {"proposed_note": note}).status_code, 422
            )
        browser = Client(enforce_csrf_checks=True)
        browser.force_login(self.owner)
        self.assertEqual(
            browser.post(
                f"/api/v1/items/{item.pk}/suggestions/preview",
                json.dumps({"proposed_note": "X"}),
                content_type="application/json",
            ).status_code,
            403,
        )
