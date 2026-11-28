from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from catalog.models import Item, ItemTopic, Topic
from . import reranking
from .services import SearchFilters, SearchService


class AdmissionTests(SimpleTestCase):
    def test_candidate_needs_both_an_absolute_score_and_a_lead(self):
        for scores, expected in [((-6, -2.1), None), ((0, 0.9), None), ((-4, -2), 0),
                                 ((-4, 2, 2), 0), (None, None)]:
            with self.subTest(scores=scores), patch.object(reranking, "_infer", return_value=scores):
                extra = ["first", "second"] if scores and len(scores) == 3 else ["first"]
                self.assertEqual(reranking.best_addition("query", ["old"], extra), expected)


@override_settings(SEARCH_MEMORY_CANDIDATES=True, SEARCH_BGE_MODEL_DIR="fixture")
class CandidateSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.owner = users.create_user(username="additional-reader")
        other = users.create_user(username="additional-other")
        topic = Topic.objects.create(owner=cls.owner, name="Ngăn thuyền")

        def note(title, *, owner=cls.owner, tagged=True, trashed=False):
            item = Item.objects.create(owner=owner, kind=Item.Kind.TEXT, title=title,
                                       deleted_at=timezone.now() if trashed else None)
            if tagged:
                ItemTopic.objects.create(item=item, topic=topic)
            return item

        cls.original = note("Dây buồm để trong hòm")
        cls.extra = note("Bậc lên mạn ở lối sau")
        excluded = note("Cất mạn cạnh cọc loại trừ")
        note("Đo mạn của chủ khác", owner=other)
        note("Bản vẽ mạn đã xóa", trashed=True)
        note("Phiếu mạn ở ngăn khác", tagged=False)
        cls.filters = SearchFilters(cls.owner.pk, topic_id=topic.pk, exclude_item_id=excluded.pk)
        cls.query = "dây buồm mạn thuyền"

    @patch("search.reranking.best_addition", return_value=0)
    def test_only_clicked_partial_first_page_can_nominate_a_visible_source(self, admit):
        service = SearchService()
        initial = service.search(self.filters, self.query)
        self.assertEqual(initial.hits, ())
        self.assertTrue(initial.can_expand)
        with self.settings(SEARCH_MEMORY_CANDIDATES=False):
            self.assertEqual(service.search(self.filters, self.query), initial)
            control = service.search(self.filters, self.query, expand=True)
        self.assertEqual([h.item_id for h in control.hits], [self.original.pk])
        for args in ({"limit": 1}, {"allow_partial": False}):
            self.assertNotIn(self.extra.pk, [h.item_id for h in service.search(
                self.filters, self.query, expand=True, **args).hits])
        self.assertEqual(service.search(self.filters, "mạn thuyền 933", expand=True).hits, ())
        admit.assert_not_called()
        page = service.search(self.filters, self.query, expand=True)
        self.assertEqual([h.item_id for h in page.hits], [self.extra.pk, self.original.pk])
        self.assertIsNone(page.next_cursor)
        self.assertEqual(page.ranking, "bge")
        self.assertIn("mạn", page.hits[0].evidence[0].snippet)
        self.assertEqual(admit.call_args.args[2], [self.extra.title])

    @patch("search.reranking.best_addition", return_value=None)
    def test_failed_or_low_scoring_challenger_keeps_the_old_page(self, admit):
        service = SearchService()
        with self.settings(SEARCH_MEMORY_CANDIDATES=False):
            old = service.search(self.filters, self.query, expand=True)
        self.assertEqual(service.search(self.filters, self.query, expand=True), old)
        admit.assert_called_once()
