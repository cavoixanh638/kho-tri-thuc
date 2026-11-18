import unicodedata
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.utils import timezone

from catalog.models import Item, ItemProject, ItemTag, ItemTopic, Project, Tag, Topic
from ingestion.models import CaptureEvent
from processing.models import DerivedContent

from .queries import SEARCH_SQL
from .services import SearchFilters, SearchService, _search_params


class SearchServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.owner = users.create_user(username="search-owner")
        cls.other = users.create_user(username="search-other")
        cls.filters = SearchFilters(owner_id=cls.owner.pk)

    def setUp(self):
        self.service = SearchService()

    def item(self, **kwargs):
        fields = {"owner": self.owner, "kind": Item.Kind.TEXT, **kwargs}
        return Item.objects.create(**fields)

    def extract(self, item, text, **kwargs):
        fields = {
            "item": item,
            "kind": "pdf_text",
            "text": text,
            "processor": "fixture",
            "processor_version": "1",
            "input_hash": "a" * 64,
            **kwargs,
        }
        return DerivedContent.objects.create(**fields)

    def capture(self, item, raw_text, **kwargs):
        fields = {
            "owner": self.owner,
            "item": item,
            "raw_kind": CaptureEvent.Kind.LINK,
            "original_url": "https://example.test/source",
            "raw_text": raw_text,
            **kwargs,
        }
        return CaptureEvent.objects.create(**fields)

    def hits(self, query, filters=None):
        return self.service.search(filters or self.filters, query).hits

    def test_vietnamese_case_accents_and_unicode_normalization(self):
        metadata = self.item(title=unicodedata.normalize("NFD", "Địa điểm Đà Nẵng"))
        extracted = self.item()
        self.extract(extracted, "địa điểm ở Đà Nẵng")

        for query in ("ĐỊA ĐIỂM", "dia diem", "địa điểm", "Da Nang"):
            with self.subTest(query=query):
                self.assertEqual({hit.item_id for hit in self.hits(query)}, {
                    metadata.pk, extracted.pk,
                })

    def test_merges_item_and_extraction_preserving_evidence(self):
        item = self.item(description="Nghiên cứu tài nguyên một cách độc lập")
        content = self.extract(
            item, "Đánh giá tài nguyên ở khu vực bờ biển",
            source_locator={"page": 12}, processor_version="2",
        )
        self.extract(item, "tài nguyên", status=DerivedContent.Status.STALE)
        self.extract(item, "tài nguyên", status=DerivedContent.Status.FAILED)

        hit, = self.hits("tai nguyen")
        self.assertEqual(hit.item_id, item.pk)
        sources = {evidence.source: evidence for evidence in hit.evidence}
        self.assertEqual(set(sources), {"item", "derived_content"})
        derived = sources["derived_content"]
        self.assertIn("tài nguyên", derived.snippet)
        self.assertEqual(derived.locator, {"page": 12})
        self.assertEqual(derived.provenance["derived_content_id"], content.pk)
        self.assertEqual(derived.provenance["processor_version"], "2")
        self.assertEqual(derived.provenance["input_hash"], "a" * 64)

    def test_item_edits_and_extraction_replacement_update_matches(self):
        item = self.item(title="Hồ sơ đóng dấu", note="sao chép cũ")
        old = self.extract(item, "bản trích cũ bị hủy")
        self.assertEqual(len(self.hits("dong dau")), 1)
        self.assertEqual(len(self.hits("sao chep cu")), 1)
        self.assertEqual(len(self.hits("bi huy")), 1)

        item.title = "Hồ sơ ký số"
        item.note = "chuyển lưu trữ"
        item.save(update_fields=["title", "note"])
        old.status = DerivedContent.Status.STALE
        old.save(update_fields=["status"])
        current = self.extract(item, "biên bản điện tử")
        self.extract(item, "tài liệu hỏng", status=DerivedContent.Status.FAILED)

        for query in ("dong dau", "sao chep cu", "bi huy", "tai lieu hong"):
            with self.subTest(query=query):
                self.assertEqual(self.hits(query), ())
        for query in ("ky so", "chuyen luu tru", "bien ban dien tu"):
            with self.subTest(query=query):
                self.assertEqual([hit.item_id for hit in self.hits(query)], [item.pk])

        DerivedContent.objects.filter(pk=current.pk).update(text="phụ lục đã duyệt")
        self.assertEqual(self.hits("bien ban dien tu"), ())
        self.assertEqual(len(self.hits("phu luc da duyet")), 1)

    def test_identifier_substring_and_typo_fallback(self):
        item = self.item(title="Quyết định 123/QĐ-UBND", note="Lưu hồ sơ handbook")
        # The partial identifier cannot be found by the plain FTS query alone.
        for query in ("123/QD-UB", "123/QĐ-UBND", "handbok"):
            with self.subTest(query=query):
                hit, = self.hits(query)
                self.assertEqual(hit.item_id, item.pk)
        self.assertEqual(self.hits("123/%UB"), ())

    def test_owner_soft_delete_and_group_intersection_apply_to_every_source(self):
        topic = Topic.objects.create(owner=self.owner, name="Topic")
        project = Project.objects.create(owner=self.owner, name="Project")
        tag = Tag.objects.create(owner=self.owner, name="Tag")
        outside_tag = Tag.objects.create(owner=self.other, name="Tag")
        good = self.item(title="Bản tổng hợp niên giám")
        wrong_group = self.item(title="Bản tổng hợp niên giám")
        deleted = self.item(title="Bản tổng hợp niên giám", deleted_at=timezone.now())
        foreign = self.item(owner=self.other, title="Bản tổng hợp niên giám")

        for item in (good, wrong_group, deleted, foreign):
            self.extract(item, "trích xuất niên giám")
            self.capture(item, "chú thích niên giám")
            ItemTopic.objects.create(item=item, topic=topic)
            ItemProject.objects.create(item=item, project=project)
            ItemTag.objects.create(item=item, tag=outside_tag if item == wrong_group else tag)

        self.assertEqual({h.item_id for h in self.hits("nien giam")}, {good.pk, wrong_group.pk})
        scoped = SearchFilters(self.owner.pk, topic.pk, project.pk, tag.pk)
        self.assertEqual([h.item_id for h in self.hits("nien giam", scoped)], [good.pk])
        self.assertEqual(self.hits("nien giam", SearchFilters(self.owner.pk, tag_id=outside_tag.pk)), ())
        self.assertEqual(self.hits("nien giam", SearchFilters(
            self.owner.pk, topic.pk, project.pk, tag.pk, exclude_item_id=good.pk,
        )), ())

    def test_annotation_provenance_original_text_and_scan_bound(self):
        item = self.item(kind=Item.Kind.LINK)
        older = self.capture(item, "Thảo luận ghi chú hiếm")
        self.capture(item, "Chú thích gửi lại")
        self.capture(item, "Thảo luận bí mật", owner=self.other)
        self.capture(
            item, "Thảo luận đã sửa",
            raw_kind=CaptureEvent.Kind.TEXT, original_url="",
        )

        hit, = self.hits("thao luan")
        evidence, = hit.evidence
        self.assertEqual(evidence.source, "capture_event")
        self.assertEqual(evidence.provenance["capture_event_id"], str(older.pk))
        self.assertIn("server_received_at", evidence.provenance)
        self.assertIn("Thảo luận", evidence.snippet)
        self.assertEqual(self.hits("bi mat"), ())
        self.assertEqual(self.hits("da sua"), ())
        # The newer visible link annotation uses up the one-row history window.
        with patch("search.services.CAPTURE_SCAN_LIMIT", 1):
            self.assertEqual(self.hits("thao luan"), ())

    def test_keyset_pages_do_not_repeat_items_at_equal_scores(self):
        items = [self.item(title="xylophone") for _ in range(3)]
        for item in items:
            self.extract(item, "xylophone")

        first = self.service.search(self.filters, "xylophone", limit=2)
        second = self.service.search(self.filters, "xylophone", first.next_cursor, limit=2)
        ids = [hit.item_id for page in (first, second) for hit in page.hits]
        self.assertEqual(ids, sorted((item.pk for item in items), reverse=True))
        self.assertIsNotNone(first.next_cursor)
        self.assertIsNone(second.next_cursor)

    def test_query_validation(self):
        self.assertEqual(self.hits("   --   "), ())
        self.assertEqual(self.hits("'%_\\'"), ())
        for query in ("\0unsafe", "a" * 301):
            with self.subTest(query_length=len(query)), self.assertRaises(ValueError):
                self.hits(query)
        with self.assertRaises(ValueError):
            self.service.search(self.filters, "abc", limit=0)

    def test_explain_analyze_uses_both_fts_indexes_and_trigram_index(self):
        items = Item.objects.bulk_create([
            Item(
                owner=self.owner, kind=Item.Kind.TEXT, title=f"ordinary entry {i}",
                description="longer ordinary body " * 10,
            )
            for i in range(4000)
        ])
        DerivedContent.objects.bulk_create([
            DerivedContent(
                item=item, kind="pdf_text", text="ordinary extracted text " * 20,
                processor="fixture", processor_version="1", input_hash=str(i),
            )
            for i, item in enumerate(items)
        ])
        target = self.item(title="quasarneedle 123/QĐ-UBND")
        self.extract(target, "quasarneedle")

        with connection.cursor() as db_cursor:
            # Flush pending writes as autovacuum would on a settled corpus.
            for index in ("kt_item_fts_gin", "kt_derived_fts_gin", "kt_item_trgm_gin"):
                db_cursor.execute("SELECT gin_clean_pending_list(%s::regclass)", [index])
            db_cursor.execute("ANALYZE catalog_item")
            db_cursor.execute("ANALYZE processing_derivedcontent")
            plans = {}
            for query in ("quasarneedle", "123/QD-UB"):
                db_cursor.execute(
                    "EXPLAIN (ANALYZE, BUFFERS) " + SEARCH_SQL,
                    _search_params(self.filters, query, None, 20),
                )
                plans[query] = "\n".join(row[0] for row in db_cursor.fetchall())

        self.assertIn("Bitmap Index Scan on kt_item_fts_gin", plans["quasarneedle"])
        self.assertIn("Bitmap Index Scan on kt_derived_fts_gin", plans["quasarneedle"])
        self.assertIn("Bitmap Index Scan on kt_item_trgm_gin", plans["123/QD-UB"])
