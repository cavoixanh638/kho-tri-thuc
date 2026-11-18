from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from catalog.models import Item, ItemTopic, Topic


class SearchApiTests(TestCase):
    def test_text_and_group_browse_with_owner_scope_and_filter_cursor(self):
        users = get_user_model().objects
        owner = users.create(username="owner")
        another = users.create(username="other")
        active = [
            Item.objects.create(owner=owner, kind=Item.Kind.TEXT, title=title)
            for title in ("Đô thị số", "Quy hoạch mới")
        ]
        hidden = Item.objects.create(
            owner=owner, kind=Item.Kind.TEXT, title="Đô thị", deleted_at=timezone.now()
        )
        private = Item.objects.create(
            owner=another, kind=Item.Kind.TEXT, title="Đô thị"
        )
        topic = Topic.objects.create(owner=owner, name="Quy hoạch")
        for item in [*active, hidden, private]:
            ItemTopic.objects.create(item=item, topic=topic)
        self.assertEqual(
            self.client.get("/api/v1/search", {"q": "do thi"}).status_code, 401
        )
        self.client.force_login(owner)
        full_text = self.client.get("/api/v1/search", {"q": "do thi"})
        self.assertEqual(full_text.status_code, 200)
        self.assertEqual(
            [row["item_id"] for row in full_text.json()["results"]], [str(active[0].pk)]
        )

        first = self.client.get(
            "/api/v1/search", {"topic_id": topic.pk, "limit": 1}
        ).json()
        self.assertEqual(len(first["results"]), 1)
        cursor = first["next_cursor"]
        second = self.client.get(
            "/api/v1/search",
            {
                "topic_id": topic.pk,
                "limit": 1,
                "cursor_score": cursor["score"],
                "cursor_item_id": cursor["item_id"],
            },
        ).json()
        self.assertEqual(len(second["results"]), 1)
        self.assertIsNone(second["next_cursor"])
        self.assertSetEqual(
            {row["item_id"] for row in first["results"] + second["results"]},
            {str(item.pk) for item in active},
        )

    def test_search_finds_the_end_of_a_supported_long_note(self):
        owner = get_user_model().objects.create(username="long-note-owner")
        item = Item.objects.create(
            owner=owner,
            kind=Item.Kind.TEXT,
            note=("nội dung " * 7000) + "từkhóacuốicùng",
        )
        self.client.force_login(owner)
        response = self.client.get("/api/v1/search", {"q": "từkhóacuốicùng"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [entry["item_id"] for entry in response.json()["results"]], [str(item.pk)]
        )
