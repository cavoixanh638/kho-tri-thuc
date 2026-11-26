"""KT124 PostgreSQL ownership and 100-note / 200-link contract."""

from datetime import datetime
from uuid import NAMESPACE_URL, uuid5

from config.session import session_api
from django.contrib.auth import get_user_model
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.test import TestCase, override_settings
from django.urls import path
from django.utils import timezone
from ninja import NinjaAPI

from .api import router as library_router
from .models import Item, RelatedItem, Topic
from .navigation_api import router

api = NinjaAPI(urls_namespace="kt124-navigation-tests")
api.add_router("", router)
api.add_router("", library_router)
urlpatterns = [path("api/v1/session", session_api), path("api/v1/", api.urls)]


class ExactDateEncoder(DjangoJSONEncoder):
    def default(self, value):
        if isinstance(value, datetime):
            return value.isoformat()
        return super().default(value)


@override_settings(ROOT_URLCONF=__name__)
class NavigationTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="navigation-owner")
        self.other = get_user_model().objects.create_user(username="navigation-other")
        self.client.force_login(self.owner)

    def test_hundred_notes_two_hundred_uuid_links_rename_and_roundtrip(self):
        notes = [
            Item(
                id=uuid5(NAMESPACE_URL, f"kt124-{index}"),
                owner=self.owner,
                kind="text",
                title=f"Bài tiếng Việt {index}",
            )
            for index in range(100)
        ]
        for index, item in enumerate(notes):
            item.note = f"# Bài {index}\r\nTiếng Việt nguyên văn.\r\n" + "\r\n".join(
                f"[Bài {offset}](#/muc/{notes[(index + offset) % 100].pk})"
                for offset in (1, 2)
            )
        Item.objects.bulk_create(notes)
        before = {item.pk: item.note.encode() for item in notes}
        for index, item in enumerate(notes):
            payload = self.client.get(f"/api/v1/items/{item.pk}/links").json()
            self.assertEqual(
                {hit["item_id"] for hit in payload["outgoing"]},
                {str(notes[(index + offset) % 100].pk) for offset in (1, 2)},
            )
            self.assertEqual(payload["counts"]["incoming"], 2)
        self.assertEqual(RelatedItem.objects.count(), 0)
        target = notes[1]
        for title in ("Tên mới", "Trùng tiêu đề", "Đổi lần ba"):
            target.title = title
            target.save(update_fields=["title"])
            payload = self.client.get(f"/api/v1/items/{notes[0].pk}/links").json()
            self.assertIn(
                {
                    "item_id": str(target.pk),
                    "title": title,
                    "saved_at": target.saved_at.isoformat(),
                },
                payload["outgoing"],
            )
        payload = serializers.serialize(
            "json", Item.objects.filter(owner=self.owner), cls=ExactDateEncoder
        )
        for saved in serializers.deserialize("json", payload):
            saved.save()
        self.assertEqual(Item.objects.count(), 100)
        self.assertEqual(
            {item.pk: item.note.encode() for item in Item.objects.all()}, before
        )
        self.assertEqual(
            self.client.get(f"/api/v1/items/{notes[0].pk}/links").json()["counts"][
                "outgoing"
            ],
            2,
        )

    def test_mentions_explicit_links_private_and_deleted_do_not_conflate(self):
        target = Item.objects.create(
            owner=self.owner, kind="text", title="Luật Đầu tư", note="Tri thức"
        )
        linked = Item.objects.create(
            owner=self.owner,
            kind="text",
            title="Có liên kết",
            note=f"[Luật Đầu tư](#/muc/{target.pk})",
        )
        mention = Item.objects.create(
            owner=self.owner,
            kind="text",
            title="Chỉ nhắc tên",
            note="Đọc Luật Đầu tư trước khi làm.",
        )
        private = Item.objects.create(
            owner=self.other,
            kind="text",
            title="Bí mật",
            note=f"[Luật Đầu tư](#/muc/{target.pk})",
        )
        Item.objects.create(
            owner=self.owner,
            kind="text",
            title="Đã xóa",
            note="Luật Đầu tư",
            deleted_at=timezone.now(),
        )
        payload = self.client.get(f"/api/v1/items/{target.pk}/links").json()
        self.assertEqual(
            [hit["item_id"] for hit in payload["incoming"]], [str(linked.pk)]
        )
        self.assertEqual(
            [hit["item_id"] for hit in payload["unlinked"]], [str(mention.pk)]
        )
        self.assertNotIn(str(private.pk), str(payload))
        self.assertEqual(
            Item.objects.get(pk=mention.pk).note, "Đọc Luật Đầu tư trước khi làm."
        )
        self.assertEqual(RelatedItem.objects.count(), 0)
        self.assertEqual(
            self.client.get(f"/api/v1/items/{private.pk}/links").status_code, 404
        )
        mention.note += f"\n[Không truy cập](#/muc/{private.pk})"
        mention.save(update_fields=["note"])
        hidden = self.client.get(f"/api/v1/items/{mention.pk}/links").json()
        self.assertEqual(hidden["unavailable_outgoing_count"], 1)
        self.assertEqual(hidden["outgoing"], [])
        self.assertNotIn(private.title, str(hidden))
        target.deleted_at = timezone.now()
        target.save(update_fields=["deleted_at"])
        self.assertEqual(
            self.client.get(f"/api/v1/items/{target.pk}/links").status_code, 404
        )
        self.client.logout()
        self.assertEqual(self.client.get("/api/v1/navigation").status_code, 401)

    def test_navigation_pagination_and_duplicate_titles_do_not_leak_body_or_owner(self):
        items = [
            Item(
                owner=self.owner,
                kind="text",
                title="Trùng tiêu đề",
                note="Riêng tư" * 1000,
            )
            for _ in range(25)
        ]
        Item.objects.bulk_create(items)
        Item.objects.create(
            owner=self.other, kind="text", title="Trùng tiêu đề", note="Other"
        )
        Topic.objects.create(owner=self.owner, name="Pháp luật")
        Topic.objects.create(owner=self.other, name="Pháp luật bí mật")
        Topic.objects.create(owner=self.owner, name="Archive", archived=True)
        page = self.client.get("/api/v1/navigation", {"q": "Trùng"}).json()
        self.assertEqual(len(page["items"]), 20)
        self.assertEqual(len({row["item_id"] for row in page["items"]}), 20)
        self.assertNotIn("note", page["items"][0])
        second = self.client.get(
            "/api/v1/navigation", {"q": "Trùng", "offset": page["next_offset"]}
        ).json()
        self.assertEqual(len(second["items"]), 5)
        self.assertFalse(
            {row["item_id"] for row in page["items"]}
            & {row["item_id"] for row in second["items"]}
        )
        folders = self.client.get("/api/v1/navigation", {"kind": "folders"}).json()
        self.assertEqual([row["name"] for row in folders["folders"]], ["Pháp luật"])
        for query in ({"q": "\0"}, {"q": "x" * 201}, {"offset": -1}):
            self.assertEqual(
                self.client.get("/api/v1/navigation", query).status_code, 422
            )
        self.assertEqual(
            self.client.get("/api/v1/navigation", {"kind": "sql"}).status_code, 422
        )


    def test_tab_metadata_is_bounded_owner_scoped_ordered_and_read_only(self):
        a = Item.objects.create(owner=self.owner, kind="text", title="Một", note="Raw A")
        b = Item.objects.create(owner=self.owner, kind="text", title="Hai", note="Raw B")
        hidden = Item.objects.create(owner=self.other, kind="text", title="Không lộ")
        deleted = Item.objects.create(
            owner=self.owner, kind="text", title="Đã xóa", deleted_at=timezone.now()
        )
        ids = ",".join(str(row.pk) for row in (b, hidden, a, deleted, b))
        response = self.client.get("/api/v1/navigation/tabs", {"ids": ids})
        self.assertEqual(response.status_code, 200)
        rows = response.json()["items"]
        self.assertEqual([row["item_id"] for row in rows], [str(b.pk), str(a.pk)])
        self.assertEqual([row["title"] for row in rows], ["Hai", "Một"])
        self.assertTrue(all(set(row) == {"item_id", "title", "saved_at"} for row in rows))
        self.assertNotIn("Không lộ", response.content.decode())
        self.assertNotIn("Raw", response.content.decode())
        self.assertEqual(Item.objects.count(), 4)
        for invalid in ("", "bad", ",".join([str(a.pk)] * 21), "x" * 36):
            self.assertEqual(self.client.get("/api/v1/navigation/tabs", {"ids": invalid}).status_code, 422)
        self.client.logout()
        self.assertEqual(self.client.get("/api/v1/navigation/tabs", {"ids": str(a.pk)}).status_code, 401)
