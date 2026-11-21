"""P10 KT124 independent owner/UUID/parser regression tests.

Uses the existing KT124 URLconf and a disposable Django test PostgreSQL database.
Command: python apps/backend/manage.py test catalog.test_parallel_navigation
"""
from unittest import expectedFailure
from uuid import NAMESPACE_URL, uuid5

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from .groups_api import _inline_item_links
from .models import Item, RelatedItem


@override_settings(ROOT_URLCONF="catalog.test_navigation")
class ParallelNavigationAuditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="p10-owner")
        cls.other = get_user_model().objects.create_user(username="p10-other")

    def setUp(self):
        self.client.force_login(self.owner)

    def links(self, item):
        response = self.client.get(f"/api/v1/items/{item.pk}/links")
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def test_100_notes_200_uuid_links_rename_duplicate_delete(self):
        ids = [uuid5(NAMESPACE_URL, f"p10-note-{i:03d}") for i in range(100)]
        rows = [
            Item(id=ids[i], owner=self.owner, kind="text",
                 title="Trùng tiêu đề" if i in (10, 11) else f"Bài {i} tiếng Việt",
                 note="\r\n".join(
                     f"[Bài](#/muc/{ids[(i + shift) % 100]})" for shift in (1, 2)))
            for i in range(100)
        ]
        Item.objects.bulk_create(rows)
        original = {row.pk: row.note.encode("utf-8") for row in rows}
        self.assertEqual(sum(row.note.count("](#/muc/") for row in rows), 200)
        for i, row in enumerate(rows):
            data = self.links(row)
            self.assertEqual(
                {hit["item_id"] for hit in data["outgoing"]},
                {str(ids[(i + 1) % 100]), str(ids[(i + 2) % 100])},
            )
            self.assertEqual(data["counts"]["incoming"], 2)
        target = rows[10]
        target.title = "Đổi tên không đổi UUID"
        target.save(update_fields=["title"])
        self.assertIn(target.title, [hit["title"] for hit in self.links(rows[9])["outgoing"]])
        self.assertEqual({row.pk: row.note.encode("utf-8") for row in Item.objects.all()}, original)
        target.deleted_at = timezone.now()
        target.save(update_fields=["deleted_at"])
        outgoing = self.links(rows[9])
        self.assertEqual(outgoing["counts"]["outgoing"], 1)
        self.assertEqual(outgoing["unavailable_outgoing_count"], 1)
        self.assertEqual(self.client.get(f"/api/v1/items/{target.pk}/links").status_code, 404)
        self.assertFalse(RelatedItem.objects.exists())

    def test_cross_user_deleted_missing_uuid_no_disclosure(self):
        visible = Item.objects.create(owner=self.owner, kind="text", title="Visible")
        private = Item.objects.create(owner=self.other, kind="text", title="PRIVATE_SENTINEL")
        deleted = Item.objects.create(owner=self.owner, kind="text",
                                      title="DELETED_SENTINEL", deleted_at=timezone.now())
        missing = uuid5(NAMESPACE_URL, "p10-never-created")
        source = Item.objects.create(
            owner=self.owner, kind="text", title="Source",
            note=" ".join(f"[Bài](#/muc/{id_})"
                          for id_ in (visible.pk, private.pk, deleted.pk, missing)),
        )
        result = self.links(source)
        self.assertEqual([hit["item_id"] for hit in result["outgoing"]], [str(visible.pk)])
        self.assertEqual(result["unavailable_outgoing_count"], 3)
        self.assertNotIn("PRIVATE_SENTINEL", str(result))
        self.assertNotIn("DELETED_SENTINEL", str(result))
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(f"/api/v1/items/{source.pk}/links").status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get("/api/v1/navigation").status_code, 401)

    def test_lexical_unlinked_not_a_parent_or_backlink(self):
        target = Item.objects.create(owner=self.owner, kind="text", title="Khu thương mại tự do")
        linked = Item.objects.create(owner=self.owner, kind="text",
                                     title="Linked", note=f"[Mở](#/muc/{target.pk})")
        mention = Item.objects.create(owner=self.owner, kind="text",
                                      title="Mention", note="Khu thương mại tự do")
        Item.objects.create(owner=self.other, kind="text", title="Private",
                            note="Khu thương mại tự do")
        result = self.links(target)
        self.assertEqual([row["item_id"] for row in result["incoming"]], [str(linked.pk)])
        self.assertEqual([row["item_id"] for row in result["unlinked"]], [str(mention.pk)])
        self.assertEqual(result["scope"], "explicit_inline_markdown; mentions_are_candidates_only")
        self.assertIsNone(mention.parent_item_id)
        self.assertFalse(RelatedItem.objects.exists())

    def test_code_fences_images_html_escaped_links_not_edges(self):
        uid = uuid5(NAMESPACE_URL, "p10-parser")
        link = f"[Bài](#/muc/{uid})"
        tick = "\x60"
        rejected = [
            tick * 3 + "\n" + link + "\n" + tick * 3,
            "~~~~\n" + link + "\n~~~~",
            "    " + link, tick + link + tick, "\\" + link,
            "![alt](#/muc/" + str(uid) + ")",
            "<!-- " + link + " -->", "<script>" + link + "</script>",
            "<pre>" + link + "</pre>", "[x](javascript:alert(1))",
        ]
        for text in rejected:
            with self.subTest(text=text):
                self.assertEqual(_inline_item_links(text), set())
        self.assertEqual(_inline_item_links("Xem thêm " + link), {uid})

    @expectedFailure  # P10-F01: valid Markdown adjacent to punctuation is dropped
    def test_known_gap_punctuation_adjacent_link(self):
        uid = uuid5(NAMESPACE_URL, "p10-adjacent")
        self.assertEqual(_inline_item_links(f"Xem:[Bài](#/muc/{uid})"), {uid})

    def test_navigation_owner_scope_and_invalid_queries(self):
        Item.objects.create(owner=self.owner, kind="text", title="Trùng")
        Item.objects.create(owner=self.owner, kind="text", title="Trùng")
        Item.objects.create(owner=self.other, kind="text", title="Trùng")
        result = self.client.get("/api/v1/navigation", {"kind": "items", "q": "Trùng"}).json()
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(len({row["item_id"] for row in result["items"]}), 2)
        self.assertNotIn("note", result["items"][0])
        for query in ({"q": "x" * 201}, {"q": "\0"}, {"offset": -1},
                      {"offset": 100001}, {"kind": "bad"}):
            with self.subTest(query=query):
                self.assertEqual(self.client.get("/api/v1/navigation", query).status_code, 422)
