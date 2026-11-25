from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from catalog.models import Item, ItemTopic, Topic
from .services import SearchCursor, SearchFilters, SearchService


class RememberedNoteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="recall-reader")
        cls.other = get_user_model().objects.create_user(username="recall-other")

    def note(self, title, **fields):
        fields.setdefault("owner", self.owner)
        return Item.objects.create(title=title, kind=Item.Kind.TEXT, **fields)

    def search(self, query, **kwargs):
        return SearchService().search(SearchFilters(self.owner.pk), query, **kwargs)

    def test_normal_search_form_returns_labeled_excerpt_for_remembered_words(self):
        target = self.note("Lịch trực", note="Cất áo phao bên bến tàu sau phiên trực. " * 3)
        self.note("Sai dấu", note="Dãy ghế bên Tàu xưởng.")
        query = "Mình nhớ bến tàu có áo nổi?"
        self.assertEqual(self.search(query, allow_partial=False).hits, ())
        self.client.force_login(self.owner)
        page = self.client.get("/api/v1/search", {"q": query}).json()
        self.assertEqual(page["match_kind"], "partial")
        self.assertEqual([row["item_id"] for row in page["results"]], [str(target.pk)])
        evidence, = page["results"][0]["evidence"]
        self.assertEqual(evidence["source"], "item")
        self.assertIn("bến tàu", evidence["snippet"])
        self.assertEqual(self.search("minh nho ao phao luc nao").hits[0].item_id, target.pk)

    def test_scoped_pagination_and_exclusion_use_the_same_visible_notes(self):
        topic = Topic.objects.create(owner=self.owner, name="Ca trực")
        good = [self.note("Móc dây", note="Cất buồm trước bão") for _ in range(3)]
        outside = self.note("Móc dây", note="Cất buồm trước bão")
        deleted = self.note("Móc dây", note="Cất buồm trước bão", deleted_at=timezone.now())
        foreign = self.note("Móc dây", note="Cất buồm trước bão", owner=self.other)
        for item in [*good, deleted, foreign]:
            ItemTopic.objects.create(topic=topic, item=item)
        filters = SearchFilters(self.owner.pk, topic_id=topic.pk, exclude_item_id=good[0].pk)
        service = SearchService()
        query = "dây buồm mạn thuyền"
        first = service.search(filters, query, limit=1)
        second = service.search(filters, query, first.next_cursor, limit=1)
        self.assertEqual((first.match_kind, second.match_kind), ("partial", "partial"))
        self.assertIsNone(second.next_cursor)
        self.assertEqual({first.hits[0].item_id, second.hits[0].item_id}, {good[1].pk, good[2].pk})
        self.assertNotIn(outside.pk, {first.hits[0].item_id, second.hits[0].item_id})

    def test_strict_match_keeps_precedence_including_at_end_of_pages(self):
        exact = self.note("cất buồm trước bão")
        self.note("cất buồm sau cảng")
        page = self.search("cất buồm trước bão")
        self.assertEqual([hit.item_id for hit in page.hits], [exact.pk])
        self.assertEqual(page.match_kind, "standard")
        after = SearchCursor(page.hits[0].score, exact.pk)
        self.assertEqual(self.search("cất buồm trước bão", cursor=after).hits, ())

    def test_common_terms_alone_cannot_nominate_arbitrary_documents(self):
        for _ in range(3):
            self.note("sổ tay", note="gấp vải")
        target = self.note("Gấp vải màu chàm")
        with patch("search.recall.MAX_POSTINGS_PER_TERM", 2):
            self.assertFalse(self.search("gấp vải ngăn kéo").hits)
            page = self.search("gấp vải chàm ngăn kéo")
        self.assertEqual([hit.item_id for hit in page.hits], [target.pk])

    def test_query_numbers_and_identifiers_must_be_present(self):
        target = self.note("Sổ xe AX173", note="Thay lốp ở xưởng số 14.")
        self.assertEqual(self.search("mình nhớ ghi chú AX173 hôm nào").hits[0].item_id, target.pk)
        for query in ("sổ thay lốp AX179", "sổ thay lốp 17", "sổ lốp AX/179"):
            with self.subTest(query=query):
                self.assertFalse(self.search(query).hits)
