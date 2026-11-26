from django.contrib.auth import get_user_model
from django.test import TestCase

from catalog.models import Item
from ingestion.models import CaptureEvent
from processing.models import DerivedContent
from .services import SearchFilters, SearchService


class IdentifierSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.owner = users.create_user(username="identifier-reader")
        cls.other = users.create_user(username="identifier-other")

    def note(self, title, *, body="", owner=None):
        return Item.objects.create(owner=owner or self.owner, kind=Item.Kind.TEXT, title=title, note=body)

    def found(self, query, **kwargs):
        result = SearchService().search(SearchFilters(self.owner.pk), query, **kwargs)
        return {hit.title for hit in result.hits}

    def test_alphanumeric_key_is_a_whole_token_in_normal_and_expanded_search(self):
        target = self.note("Tem (AX173).")
        for other in ("AX1730", "QAX173", "AX0173", "AX173B"):
            self.note("Tem " + other)
        self.note("Phiếu ở kho người khác AX173", owner=self.other)
        for expand in (False, True):
            with self.subTest(expand=expand):
                self.assertEqual(self.found("ax173", expand=expand), {target.title})

    def test_leading_zero_and_neighbouring_digit_sequences_remain_distinct(self):
        for value in ("173", "0173", "1730", "B0173"):
            self.note("Số phiếu " + value)
        for value in ("173", "0173", "1730"):
            with self.subTest(value=value):
                self.assertEqual(self.found(value), {"Số phiếu " + value})

    def test_codes_and_numbers_embedded_in_sentences(self):
        right = self.note("Giấy kiểm kê AX173", body="Chuyển phiếu số 173 đến bến.")
        self.note("Giấy kiểm kê AX1730", body="Chuyển phiếu số 1730 đến bến.")
        self.note("Giấy kiểm kê AX0173", body="Chuyển phiếu số 0173 đến bến.")
        queries = ("kiểm kê AX173", "phiếu số 173",
                   "tôi nhớ kiến nghị ở bến liên quan AX173")
        for query in queries:
            with self.subTest(query=query):
                self.assertEqual(self.found(query, expand=True), {right.title})
        self.assertFalse(self.found("phiếu kiểm kê AX119", expand=True))
        self.assertFalse(self.found("phiếu kiểm kê 179", expand=True))

    def test_document_prefix_starts_at_the_document_number(self):
        right = self.note("Quyết định 123/QĐ-UBND.")
        self.note("Quyết định 0123/QĐ-UBND.")
        self.note("Quyết định 4123/QĐ-UBND.")
        self.note("Ký hiệu tách riêng 123", body="Kiểm tra bảng QĐ-UBND.")
        for query in ("123/QD-UB", "123/QĐ-UBND"):
            with self.subTest(query=query):
                self.assertEqual(self.found(query), {right.title})

    def test_document_year_must_belong_to_the_same_identifier(self):
        right = self.note("Phụ lục 123/QĐ-UBND/2024")
        self.note("Phụ lục 123/QĐ-UBND/2023", body="Kiểm điểm việc thực hiện năm 2024.")
        self.note("Phụ lục 123/QĐ-UBND/20240")
        self.note("Phụ lục 0123/QĐ-UBND/2024")
        for query in ("123/QĐ-UBND/2024", "phụ lục 123/QD-UBND/2024"):
            with self.subTest(query=query):
                self.assertEqual(self.found(query, expand=True), {right.title})

    def test_hyphenated_code_does_not_match_scattered_parts(self):
        right = self.note("Phiếu AX-173")
        self.note("Bảng AX với mục thử -173")
        self.note("Phiếu AX-1730")
        self.note("Phiếu TAX-173")
        self.assertEqual(self.found("AX-173", expand=True), {right.title})

    def test_each_source_has_to_contain_the_same_document_key(self):
        right = "Biên bản AX-173"
        nearby = "Bảng AX có trị số -173"
        expected = {}
        for channel in ("item", "derived_content", "capture_event"):
            item = self.note(f"Phụ lục {channel}", body=right if channel == "item" else nearby)
            DerivedContent.objects.create(
                item=item, kind="pdf_text", processor="fixture", processor_version="1",
                input_hash="a" * 64, text=right if channel == "derived_content" else nearby,
            )
            CaptureEvent.objects.create(
                item=item, owner=self.owner, raw_kind=CaptureEvent.Kind.LINK,
                original_url="https://example.test/fixture",
                raw_text=right if channel == "capture_event" else nearby,
            )
            expected[item.pk] = {channel}
        page = SearchService().search(SearchFilters(self.owner.pk), "AX-173")
        self.assertEqual({hit.item_id: {e.source for e in hit.evidence} for hit in page.hits}, expected)
