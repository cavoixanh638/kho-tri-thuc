import unicodedata
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from catalog.models import Item, ItemProject, ItemTag, ItemTopic, Project, Tag, Topic
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
        offered = service.search(filters, query, limit=1)
        self.assertEqual(offered.hits, ())
        self.assertTrue(offered.can_expand)
        first = service.search(filters, query, limit=1, expand=True)
        second = service.search(filters, query, first.next_cursor, limit=1, expand=True)
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
            page = self.search("gấp vải chàm ngăn kéo", expand=True)
        self.assertEqual([hit.item_id for hit in page.hits], [target.pk])

    def test_query_numbers_and_identifiers_must_be_present(self):
        target = self.note("Sổ xe AX173", note="Thay lốp ở xưởng số 14.")
        self.assertEqual(self.search("mình nhớ ghi chú AX173 hôm nào").hits[0].item_id, target.pk)
        for query in ("sổ thay lốp AX179", "sổ thay lốp 17", "sổ lốp AX/179"):
            with self.subTest(query=query):
                self.assertFalse(self.search(query, expand=True).hits)

    def test_weak_overlap_is_offered_only_on_request(self):
        target = self.note("Sổ tay đi biển", note="Xếp áo phao trên bờ.")
        query = "mình tìm áo nổi để xuống bờ"
        self.client.force_login(self.owner)
        default = self.client.get("/api/v1/search", {"q": query}).json()
        self.assertEqual(default["results"], [])
        self.assertTrue(default["can_expand"])
        expanded = self.client.get("/api/v1/search", {"q": query, "expand": "true"}).json()
        self.assertEqual([r["item_id"] for r in expanded["results"]], [str(target.pk)])
        self.assertEqual(expanded["match_kind"], "partial")
        self.assertFalse(expanded["can_expand"])

    def test_mixed_accents_in_a_remembered_phrase(self):
        dock = self.note("Sổ trực", note="Đánh dấu bến tàu trên bản đồ.")
        beside = self.note("Sổ trực", note="Để thùng bên tàu đợi người nhận.")
        for marked, expected in (("bến", dock), ("bên", beside)):
            variants = [f"{marked} tau mép vách", unicodedata.normalize("NFD", f"{marked.upper()}\u00a0TAU\tmép vách")]
            for query in variants:
                with self.subTest(query=query):
                    first = self.search(query)
                    self.assertEqual(first.hits, ())
                    self.assertTrue(first.can_expand)
                    result = self.search(query, expand=True)
                    self.assertEqual([hit.item_id for hit in result.hits], [expected.pk])
                    self.assertIn(f"{marked} tàu", result.hits[0].evidence[0].snippet)

    def test_spelling_the_same_clue_twice_does_not_create_two_clues(self):
        self.note("Nhật ký ca tối", note="Gặp nhau ở bến.")
        for query in ("bến ben triền gỗ", "ben bến triền gỗ", "BẾN bến triền gỗ"):
            with self.subTest(query=query):
                self.assertFalse(self.search(query).can_expand)
                self.assertEqual(self.search(query, expand=True).hits, ())

    def test_prose_colon_and_time_literal_have_distinct_behavior(self):
        target = self.note("Tại chỗ", note="Đánh dấu bến tàu. Ca 08 có 15 người.")
        for query in ("bến tàu mép vách", "Ghi chú: bến tàu mép vách?", "Ghi chú:\nbến tàu mép vách"):
            with self.subTest(query=query):
                self.assertTrue(self.search(query).can_expand)
                self.assertEqual([h.item_id for h in self.search(query, expand=True).hits], [target.pk])
        self.assertFalse(self.search("bến tàu hôm lạ 08:15", expand=True).hits)

    def test_edit_retag_and_trash_refresh_results_with_intersecting_filters(self):
        topic = Topic.objects.create(owner=self.owner, name="Kho")
        project = Project.objects.create(owner=self.owner, name="Bảo trì")
        tag = Tag.objects.create(owner=self.owner, name="Bàn giao")
        target = self.note("Bàn giao", note="Dỡ buồm ở bến tàu.")
        outside = self.note("Bàn giao", note="Dỡ buồm ở bến tàu.")
        for item in (target, outside):
            ItemTopic.objects.create(item=item, topic=topic)
            ItemProject.objects.create(item=item, project=project)
        assignment = ItemTag.objects.create(item=target, tag=tag)
        filters = SearchFilters(self.owner.pk, topic_id=topic.pk, project_id=project.pk, tag_id=tag.pk)

        def verify(expected):
            query = "buồm tàu ron tím"
            service = SearchService()
            self.assertEqual(service.search(filters, query).can_expand, bool(expected))
            self.assertEqual([h.item_id for h in service.search(filters, query, expand=True).hits], expected)

        verify([target.pk])
        assignment.delete()
        verify([])
        ItemTag.objects.create(item=target, tag=tag)
        Item.objects.filter(pk=target.pk).update(note="Kiểm kê ống trong kho.")
        verify([])
        Item.objects.filter(pk=target.pk).update(note="Dỡ buồm ở bến tàu.")
        verify([target.pk])
        Item.objects.filter(pk=target.pk).update(deleted_at=timezone.now())
        verify([])

    def test_candidate_frequency_boundary_is_within_the_selected_folder(self):
        items = Item.objects.bulk_create([
            Item(owner=self.owner, kind=Item.Kind.TEXT, title="Gấp vải") for _ in range(64)
        ])
        query = "gấp vải khung sườn"
        self.assertTrue(self.search(query).can_expand)
        self.note("Gấp vải")
        self.assertFalse(self.search(query).can_expand)
        self.assertTrue(self.search("gấp vải").hits)
        topic = Topic.objects.create(owner=self.owner, name="Mẫu giữ lại")
        ItemTopic.objects.create(topic=topic, item=items[0])
        scoped = SearchFilters(self.owner.pk, topic_id=topic.pk)
        page = SearchService().search(scoped, query, expand=True)
        self.assertEqual([hit.item_id for hit in page.hits], [items[0].pk])

    def test_recall_snippet_reaches_tail_of_two_notes_with_the_same_title(self):
        prefix = "Thông tin đóng gói. " * 60
        target = self.note("Phiếu giao", note=prefix + "Đã mang thước đồng lên xưởng.")
        self.note("Phiếu giao", note=prefix + "Gửi hộp chì cho đại lý.")
        page = self.search("tìm thước đồng mép cong", expand=True)
        self.assertEqual([hit.item_id for hit in page.hits], [target.pk])
        self.assertIn("thước đồng", page.hits[0].evidence[0].snippet)
