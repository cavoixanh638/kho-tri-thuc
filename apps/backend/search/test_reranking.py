import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from catalog.models import Item, ItemTopic, Topic
from . import reranking
from .services import SearchFilters, SearchService


class LocalRerankerTests(SimpleTestCase):
    def test_absent_model_retries_and_reuses_one_loaded_session(self):
        with tempfile.TemporaryDirectory() as directory, self.settings(SEARCH_BGE_MODEL_DIR=directory):
            model = Mock()
            model.order.return_value = (1, 0)
            with patch.object(reranking, "_BgeReranker", side_effect=[FileNotFoundError(), model]) as load:
                with patch.object(reranking.time, "monotonic", return_value=100):
                    with self.assertLogs(reranking.log, "WARNING") as messages:
                        self.assertIsNone(reranking.rerank_order("private query", ["sensitive", "note"]))
                    self.assertNotIn("private query", str(messages.output))
                    self.assertNotIn("sensitive", str(messages.output))
                    self.assertIsNone(reranking.rerank_order("query", ["one", "two"]))
                with patch.object(reranking.time, "monotonic", return_value=131):
                    self.assertEqual(reranking.rerank_order("query", ["one", "two"]), (1, 0))
                    self.assertEqual(reranking.rerank_order("query", ["one", "two"]), (1, 0))
                self.assertEqual(load.call_count, 2)
                load.assert_called_with(Path(directory))

    def test_small_large_and_disabled_requests_do_not_load_weights(self):
        with patch.object(reranking, "_BgeReranker") as load:
            with self.settings(SEARCH_BGE_MODEL_DIR=""):
                self.assertIsNone(reranking.rerank_order("query", ["one", "two"]))
            with self.settings(SEARCH_BGE_MODEL_DIR="unused"):
                for texts in ([], ["one"], ["candidate"] * 6):
                    self.assertIsNone(reranking.rerank_order("query", texts))
            load.assert_not_called()


@override_settings(SEARCH_BGE_MODEL_DIR="fixture")
class ExpandedRankingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="near-search-owner")
        cls.other = get_user_model().objects.create_user(username="near-search-other")
        cls.topic = Topic.objects.create(owner=cls.owner, name="Thử dây")
        cls.filters = SearchFilters(cls.owner.pk, topic_id=cls.topic.pk)
        cls.query = "dây buồm mạn thuyền"
        for label in range(12):
            item = Item.objects.create(
                owner=cls.other if label == 9 else cls.owner, title=f"Móc dây {label:02d}",
                kind=Item.Kind.TEXT, description="Sổ tay", note=f"Cất buồm trước bão, kệ {label:02d}.",
                deleted_at=timezone.now() if label == 10 else None,
            )
            if label != 11:
                ItemTopic.objects.create(item=item, topic=cls.topic)

    @patch("search.reranking.rerank_order", side_effect=lambda q, docs: tuple(reversed(range(len(docs)))))
    def test_five_already_visible_candidates_only_and_original_lexical_cursor(self, rank):
        service = SearchService()
        with self.settings(SEARCH_BGE_MODEL_DIR=""):
            expected = service.search(self.filters, self.query, expand=True, limit=5)
        initial = service.search(self.filters, self.query, limit=5)
        self.assertTrue(initial.can_expand)
        self.assertEqual(initial.ranking, "lexical")
        rank.assert_not_called()

        first = service.search(self.filters, self.query, expand=True, limit=5)
        self.assertEqual(first.hits, tuple(reversed(expected.hits)))
        self.assertEqual(first.ranking, "bge")
        self.assertEqual(first.next_cursor, expected.next_cursor)
        self.assertNotEqual(first.next_cursor.item_id, first.hits[-1].item_id)
        query, texts = rank.call_args.args
        self.assertEqual(query, self.query)
        self.assertEqual(texts, [
            hit.title + "\nSổ tay\nCất buồm trước bão, kệ " + hit.title[-2:] + "." for hit in expected.hits
        ])
        second = service.search(self.filters, self.query, first.next_cursor, expand=True, limit=5)
        self.assertEqual(second.ranking, "lexical")
        self.assertIsNone(second.next_cursor)
        self.assertEqual(len({h.item_id for h in (*first.hits, *second.hits)}), 9)
        self.assertEqual(rank.call_count, 1)

        with self.settings(SEARCH_BGE_MODEL_DIR=""):
            old = service.search(self.filters, self.query, expand=True, limit=25)
        large = service.search(self.filters, self.query, expand=True, limit=25)
        self.assertEqual(large.hits, tuple(reversed(old.hits[:5])) + old.hits[5:])
        self.assertEqual(len(rank.call_args.args[1]), 5)

    @patch("search.reranking.rerank_order", return_value=None)
    def test_unavailable_bge_is_a_lexical_page_and_api_supports_exclusion(self, rank):
        self.client.force_login(self.owner)
        query = {"q": self.query, "topic_id": self.topic.pk, "expand": "true", "limit": 5}
        response = self.client.get("/api/v1/search", query).json()
        self.assertEqual(response["ranking"], "lexical")
        self.assertEqual(len(response["results"]), 5)
        rank.assert_called_once()
        excluded = response["results"][0]["item_id"]
        for text in (self.query, ""):
            scoped = self.client.get("/api/v1/search", {**query, "q": text, "exclude_item_id": excluded}).json()
            self.assertNotIn(excluded, [h["item_id"] for h in scoped["results"]])

    @patch("search.reranking.rerank_order")
    def test_no_scoring_for_strict_hits_one_suggestion_or_empty_search(self, rank):
        service = SearchService()
        for query, limit in (("móc dây", 5), (self.query, 1), ("mã phiếu AX3917", 5)):
            page = service.search(self.filters, query, limit=limit, expand=True)
            self.assertEqual(page.ranking, "lexical")
        rank.assert_not_called()
