from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from storage.drive import DriveError
from storage.models import Asset

from .models import Item, Source

URL = "/api/v1/items"


class LibraryApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.owner = users.create(username="owner")
        cls.other = users.create(username="other")
        cls.note = Item.objects.create(
            owner=cls.owner, title="Ghi chú", kind=Item.Kind.TEXT
        )
        cls.link = Item.objects.create(
            owner=cls.owner, title="Nguồn", kind=Item.Kind.LINK, favorite=True
        )
        cls.other_note = Item.objects.create(
            owner=cls.other, title="Private", kind=Item.Kind.TEXT
        )
        Source.objects.create(
            item=cls.link,
            original_url="https://example.org/original",
            canonical_url="https://example.org/original",
            identity_hash="unit-test",
        )

    def setUp(self):
        self.client.force_login(self.owner)

    def test_list_filters_by_owner_favorite_and_pages(self):
        first = self.client.get(URL, {"limit": 1}).json()
        self.assertEqual(len(first["results"]), 1)
        self.assertEqual(first["next_offset"], 1)
        self.assertEqual(
            first["results"][0]["original_url"], "https://example.org/original"
        )
        second = self.client.get(URL, {"limit": 1, "offset": 1}).json()
        self.assertEqual(second["results"][0]["item_id"], str(self.note.pk))
        self.assertEqual(second["results"][0]["asset_storage"], "not_applicable")
        self.assertIsNone(second["next_offset"])
        self.assertEqual(
            len(self.client.get(URL, {"favorite": "true"}).json()["results"]), 1
        )
        self.assertEqual(self.client.get(URL, {"limit": 101}).status_code, 422)

    def test_detail_is_private(self):
        self.assertEqual(
            self.client.get(f"{URL}/{self.other_note.pk}").status_code, 404
        )
        self.client.logout()
        self.assertEqual(self.client.get(f"{URL}/{self.note.pk}").status_code, 401)

    def test_edit_soft_delete_and_restore_preserve_saved_time(self):
        url = f"{URL}/{self.note.pk}"
        before = self.client.get(url).json()
        changed = self.client.patch(
            url,
            {"note": "nguyên văn\n dòng hai ", "deleted": True},
            content_type="application/json",
        )
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(changed.json()["note"], "nguyên văn\n dòng hai ")
        self.assertEqual(changed.json()["saved_at"], before["saved_at"])
        self.assertEqual(len(self.client.get(URL).json()["results"]), 1)
        self.assertEqual(
            len(self.client.get(URL, {"deleted": "true"}).json()["results"]), 1
        )
        restored = self.client.patch(
            url, {"deleted": False}, content_type="application/json"
        )
        self.assertFalse(restored.json()["deleted"])
        self.note.refresh_from_db()
        self.assertEqual(self.note.user_edit_version, 1)

    @patch("catalog.api.storage_for_owner")
    def test_asset_view_is_owner_scoped_and_errors_are_safe(self, storage):
        asset = Asset.objects.create(
            item=self.link, mime="image/png", original_filename="file.png"
        )
        url = f"/api/v1/assets/{asset.pk}/open"
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        storage.assert_not_called()
        self.client.force_login(self.owner)
        storage.return_value.open.side_effect = DriveError("storage_not_verified")
        self.assertEqual(self.client.get(url).json(), {"code": "storage_not_verified"})
