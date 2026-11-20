import json

from catalog.models import Item
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone


class SuggestionCapabilitiesTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="review-host")
        self.other = get_user_model().objects.create_user(username="review-other-host")
        self.item = Item.objects.create(owner=self.owner, kind="text", note="Bản gốc")
        self.path = f"/api/v1/items/{self.item.pk}/suggestions/capabilities"

    @override_settings(SUGGESTION_REVIEW_POC_ENABLED=False)
    def test_default_disabled_owner_read_is_inert_and_no_provider(self):
        self.assertEqual(self.client.get(self.path).status_code, 401)
        self.client.force_login(self.owner)
        before = Item.objects.filter(pk=self.item.pk).values().get()
        result = self.client.get(self.path)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(
            result.json(),
            {
                "enabled": False,
                "provider_configured": False,
                "mode": "manual_review_poc",
                "receipt_ttl_seconds": 900,
            },
        )
        self.assertEqual(Item.objects.filter(pk=self.item.pk).values().get(), before)

    @override_settings(SUGGESTION_REVIEW_POC_ENABLED=True)
    def test_explicit_opt_in_remains_manual_owner_scoped_and_deleted_hidden(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.path).status_code, 404)
        self.client.force_login(self.owner)
        self.assertTrue(self.client.get(self.path).json()["enabled"])
        self.item.deleted_at = timezone.now()
        self.item.save(update_fields=["deleted_at"])
        self.assertEqual(self.client.get(self.path).status_code, 404)

    @override_settings(SUGGESTION_REVIEW_POC_ENABLED=True)
    def test_review_accept_and_editor_use_the_same_atomic_version_contract(self):
        self.client.force_login(self.owner)
        item_path = f"/api/v1/items/{self.item.pk}"

        def send(path, data, method="post"):
            return getattr(self.client, method)(
                path, json.dumps(data), content_type="application/json"
            )

        preview = send(
            item_path + "/suggestions/preview", {"proposed_note": "Đề xuất thủ công"}
        ).json()
        accepted = send(
            item_path + "/suggestions/accept", {"receipt": preview["receipt"]}
        )
        self.assertEqual(accepted.status_code, 200, accepted.content)
        version = accepted.json()["edit_version"]
        self.item.refresh_from_db()
        self.assertEqual(
            accepted.json()["updated_at"], self.item.updated_at.isoformat()
        )
        self.assertEqual(
            self.client.get(item_path).json()["user_edit_version"], version
        )
        stale = send(
            item_path,
            {"note": "Bản nháp cũ", "expected_edit_version": version - 1},
            "patch",
        )
        self.assertEqual(stale.status_code, 409)
        edited = send(
            item_path,
            {"note": "Chỉnh sửa sau duyệt", "expected_edit_version": version},
            "patch",
        )
        self.assertEqual(edited.status_code, 200, edited.content)
        undone = send(
            item_path + "/suggestions/undo",
            {"receipt": accepted.json()["undo_receipt"]},
        )
        self.assertEqual(undone.status_code, 409)
        self.item.refresh_from_db()
        self.assertEqual(self.item.note, "Chỉnh sửa sau duyệt")
        self.assertEqual(self.item.user_edit_version, version + 1)
