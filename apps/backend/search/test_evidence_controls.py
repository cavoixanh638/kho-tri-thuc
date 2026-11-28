from django.contrib.auth import get_user_model
from django.test import TestCase

from catalog.models import Item
from .services import SearchFilters, SearchService


class SearchEvidenceControlTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="evidence-control-reader")

    def note(self, text):
        return Item.objects.create(owner=self.owner, title="Phiếu vận hành", kind=Item.Kind.TEXT, note=text)

    def assert_supported(self, query, expected, span):
        service = SearchService()
        for expand in (False, True):
            with self.subTest(query=query, expand=expand):
                page = service.search(SearchFilters(self.owner.pk), query, expand=expand)
                self.assertEqual([hit.item_id for hit in page.hits], [expected.pk])
                evidence, = page.hits[0].evidence
                self.assertEqual(evidence.source, "item")
                self.assertIn(span, evidence.snippet)

                # The opposite note remains visible after the supported note is excluded.
                wrong_only = service.search(
                    SearchFilters(self.owner.pk, exclude_item_id=expected.pk), query, expand=expand
                )
                self.assertEqual(wrong_only.hits, ())
                self.assertFalse(wrong_only.can_expand)

    def test_affirmation_and_negation_each_require_the_written_polarity(self):
        pull = self.note("Kéo chốt bạc khi còi vang.")
        hold = self.note("Không kéo chốt bạc khi còi vang.")

        self.assert_supported("kéo chốt bạc khi còi vang", pull, "Kéo chốt bạc khi còi vang")
        self.assert_supported("không kéo chốt bạc khi còi vang", hold, "Không kéo chốt bạc khi còi vang")

    def test_action_is_bound_to_the_signal_that_triggers_it(self):
        amber_lowers = self.note("Khi đèn hổ phách nháy, hạ cửa cuốn. Khi chuông đồng reo, nâng cửa cuốn.")
        amber_raises = self.note("Khi đèn hổ phách nháy, nâng cửa cuốn. Khi chuông đồng reo, hạ cửa cuốn.")

        self.assert_supported(
            "đèn hổ phách nháy thì hạ cửa cuốn", amber_lowers, "đèn hổ phách nháy, hạ cửa cuốn"
        )
        self.assert_supported(
            "đèn hổ phách nháy thì nâng cửa cuốn", amber_raises, "đèn hổ phách nháy, nâng cửa cuốn"
        )

    def test_temporal_constraint_distinguishes_before_from_after(self):
        before = self.note("Tháo lưới lọc trước khi xả bồn.")
        after = self.note("Tháo lưới lọc sau khi xả bồn.")

        self.assert_supported("tháo lưới lọc trước khi xả bồn", before, "Tháo lưới lọc trước khi xả bồn")
        self.assert_supported("tháo lưới lọc sau khi xả bồn", after, "Tháo lưới lọc sau khi xả bồn")
        self.assert_supported("Ghi chú tháo lưới lọc sau khi xả bồn", after, "Tháo lưới lọc sau khi xả bồn")

    def test_preview_shows_the_supported_action_when_an_earlier_passage_forbids_it(self):
        item = self.note("Không nên kéo chốt bạc khi còi vang. " + "Kiểm kê cuối ngày. " * 80
                         + "Kéo chốt bạc khi còi vang.")
        for query in ("kéo chốt bạc khi còi vang", "không nên kéo chốt bạc khi còi vang"):
            with self.subTest(query=query):
                hit, = SearchService().search(SearchFilters(self.owner.pk), query).hits
                self.assertEqual(hit.item_id, item.pk)
                self.assertEqual(hit.evidence[0].snippet.casefold(), query)

    def test_handoff_requires_the_written_sender_and_receiver(self):
        glass_sends = self.note("Tổ kính giao khóa đồng cho tổ mộc.")
        wood_sends = self.note("Tổ mộc giao khóa đồng cho tổ kính.")

        self.assert_supported("tổ kính giao khóa đồng cho tổ mộc", glass_sends, "Tổ kính giao khóa đồng cho tổ mộc")
        self.assert_supported("tổ mộc giao khóa đồng cho tổ kính", wood_sends, "Tổ mộc giao khóa đồng cho tổ kính")

    def test_color_must_describe_the_requested_object_in_the_same_sentence(self):
        orange_hemp = self.note("Bạt gai viền cam. Bạt lanh viền lục.")
        green_hemp = self.note("Bạt gai viền lục. Bạt lanh viền cam.")

        self.assert_supported("bạt gai viền cam", orange_hemp, "Bạt gai viền cam")
        self.assert_supported("bạt gai viền lục", green_hemp, "Bạt gai viền lục")

    def test_dimensions_preserve_the_association_between_values_and_labels(self):
        wide = self.note("Khay Gió Nâu rộng 72 mm, cao 48 mm.")
        tall = self.note("Khay Gió Nâu rộng 48 mm, cao 72 mm.")

        self.assert_supported("khay Gió Nâu rộng 72 mm cao 48 mm", wide, "rộng 72 mm, cao 48 mm")
        self.assert_supported("khay Gió Nâu rộng 48 mm cao 72 mm", tall, "rộng 48 mm, cao 72 mm")

    def test_unit_letter_case_belongs_to_the_requested_measurement(self):
        byte_rate = self.note("Tốc độ mạng 32 MB/s; tốc độ máy đọc 32 Mb/s.")
        bit_rate = self.note("Tốc độ mạng 32 Mb/s; tốc độ máy đọc 32 MB/s.")

        self.assert_supported("tốc độ mạng 32 MB/s", byte_rate, "Tốc độ mạng 32 MB/s")
        self.assert_supported("tốc độ mạng 32 Mb/s", bit_rate, "Tốc độ mạng 32 Mb/s")

    def test_explicit_details_return_a_note_when_it_really_supports_them(self):
        pairs = (
            ("Đổi khay vì lớp lót cũ làm rách giấy", "Đổi khay vì lớp lót cũ làm rách giấy.",
             "Đổi khay vì cần thêm chỗ. Lớp lót cũ vẫn tốt. Giấy bị rách lúc gấp."),
            ("Hướng dẫn nhận vé chỉ bằng thẻ xanh", "Hướng dẫn nhận vé chỉ bằng thẻ xanh.",
             "Hướng dẫn nhận vé cần cả thẻ xanh lẫn giấy mời."),
            ("Hẹn giao bìa chủ nhật", "Hẹn giao bìa chủ nhật tại cửa kho.", "Hẹn giao bìa thứ bảy tại cửa kho."),
            ("song hoa nxb giọt nắng hồng", "Song Hoa, Nhà xuất bản Giọt Nắng Hồng.",
             "Song Hoa của Nhà xuất bản Giọt Nắng Xanh. Trang cuối in màu hồng."),
        )
        service = SearchService()
        for query, yes, no in pairs:
            with self.subTest(query=query):
                supported = self.note(yes)
                self.note(no)
                page = service.search(SearchFilters(self.owner.pk), query, expand=True)
                self.assertEqual([hit.item_id for hit in page.hits], [supported.pk])
                filtered = SearchFilters(self.owner.pk, exclude_item_id=supported.pk)
                self.assertFalse(service.search(filtered, query).can_expand)
                self.assertFalse(service.search(filtered, query, expand=True).hits)
