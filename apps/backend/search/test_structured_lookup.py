from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from catalog.models import Item, ItemProject, ItemTag, ItemTopic, Project, Tag, Topic
from processing.models import DerivedContent

from .services import SearchFilters, SearchService


SEARCH_MODES = (
    {"allow_partial": False},
    {"allow_partial": True},
    {"allow_partial": True, "expand": True},
)


class StructuredLookupTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.owner = users.create_user(username="structured-reader")
        cls.other = users.create_user(username="structured-other")

    def setUp(self):
        self.service = SearchService()
        self.filters = SearchFilters(self.owner.pk)

    def note(self, body, *, title="Phiếu theo dõi", owner=None, **fields):
        return Item.objects.create(
            owner=owner or self.owner, title=title, kind=Item.Kind.TEXT, note=body, **fields,
        )

    def assert_exact_note(self, query, expected, snippet):
        for mode in SEARCH_MODES:
            with self.subTest(query=query, mode=mode):
                page = self.service.search(self.filters, query, **mode)
                self.assertEqual([hit.item_id for hit in page.hits], [expected.pk])
                evidence, = page.hits[0].evidence
                self.assertEqual(evidence.source, "item")
                self.assertIn(snippet, evidence.snippet)

    def test_decimal_measurement_belongs_to_the_requested_object(self):
        target = self.note("Puly Đá Sương rộng 26,4 mm. Puly Sáo Vàng rộng 31,8 mm.")
        self.note("Puly Đá Sương rộng 31,8 mm. Puly Sáo Vàng rộng 26,4 mm.")
        self.note("Puly Sáo Vàng rộng 26,4 mm.")
        self.note("Puly Đá Sương rộng 126,4 mm.")

        self.assert_exact_note("puly Đá Sương rộng 26,4 mm", target, "26,4 mm")

    def test_whole_number_is_tied_to_the_requested_entry(self):
        target = self.note("Kệ Hạ Sa có 283 hộp. Kệ Tường Vi có 164 hộp.")
        self.note("Kệ Hạ Sa có 164 hộp. Kệ Tường Vi có 283 hộp.")
        self.note("Kệ Tường Vi có 283 hộp.")
        self.note("Kệ Hạ Sa có 0283 hộp.")

        self.assert_exact_note("kệ Hạ Sa có 283 hộp", target, "283 hộp")

    def test_date_belongs_to_the_requested_activity(self):
        signed = self.note("Ký phiếu men lam ngày 2027-08-19. Chuyển phiếu men lam ngày 2027-08-26.")
        moved = self.note("Ký phiếu men lam ngày 2027-08-26. Chuyển phiếu men lam ngày 2027-08-19.")
        self.note("Ký phiếu men ngọc ngày 2027-08-19.")
        self.assert_exact_note("ký phiếu men lam ngày 2027-08-19", signed, "2027-08-19")
        self.assert_exact_note("chuyển phiếu men lam ngày 2027-08-19", moved, "2027-08-19")

    def test_quoted_dotted_code_selects_the_complete_identifier(self):
        target = self.note("Niêm phong mang mã HN.64.8.")
        self.note("Niêm phong mang mã HN.64.80.")
        self.note("Niêm phong mang mã HN.64.8.2.")
        self.note("Niêm phong mang mã TX.64.8.")
        self.note("Niêm phong HN ở kho 64, mục 8.")

        self.assert_exact_note('"HN.64.8"', target, "HN.64.8")

    def test_quoted_version_distinguishes_release_from_neighbours(self):
        target = self.note("Pho bản lắp đặt v4.27.6.")
        self.note("Pho bản lắp đặt v4.27.60.")
        self.note("Pho bản lắp đặt v4.27.6-rc.3.")
        self.note("Pho bản lắp đặt v14.27.6.")

        self.assert_exact_note('"v4.27.6"', target, "v4.27.6")

    def test_requested_measurement_keeps_both_sign_and_unit(self):
        target = self.note("Độ lệch tấm Lưu Ly −14,6 mm.")
        self.note("Độ lệch tấm Lưu Ly +14,6 mm.")
        self.note("Độ lệch tấm Lưu Ly −14,6 cm.")
        self.note("Độ lệch tấm Lưu Ly −114,6 mm.")

        self.assert_exact_note("độ lệch tấm Lưu Ly -14,6 mm", target, "−14,6 mm")

    def test_scoped_pages_keep_matching_sources_and_exclude_ineligible_items(self):
        topic = Topic.objects.create(owner=self.owner, name="Khu thử kính")
        project = Project.objects.create(owner=self.owner, name="Đo độ lệch")
        tag = Tag.objects.create(owner=self.owner, name="Đã đo")
        filters = SearchFilters(self.owner.pk, topic_id=topic.pk, project_id=project.pk, tag_id=tag.pk)

        ascii_reading = "Độ lệch kính Tảo Biển -12,7 mm."
        unicode_reading = "Độ lệch kính Tảo Biển −12,7 mm."
        note = self.note(ascii_reading)
        extracted = self.note("Tập bản vẽ.")
        content = DerivedContent.objects.create(
            item=extracted, kind="pdf_text", text=unicode_reading,
            processor="fixture", processor_version="2", input_hash="b" * 64,
            source_locator={"page": 17},
        )
        outside = self.note(ascii_reading)
        deleted = self.note(ascii_reading, deleted_at=timezone.now())
        foreign = self.note(ascii_reading, owner=self.other)
        wrong_sign = self.note("Độ lệch kính Tảo Biển +12,7 mm.")
        for item in (note, extracted, outside, deleted, foreign, wrong_sign):
            ItemTopic.objects.create(topic=topic, item=item)
            ItemProject.objects.create(project=project, item=item)
        for item in (note, extracted, deleted, foreign, wrong_sign):
            ItemTag.objects.create(tag=tag, item=item)

        query = "độ lệch kính Tảo Biển -12,7 mm"
        for mode in SEARCH_MODES:
            with self.subTest(mode=mode):
                first = self.service.search(filters, query, limit=1, **mode)
                self.assertIsNotNone(first.next_cursor)
                second = self.service.search(filters, query, first.next_cursor, limit=1, **mode)
                self.assertEqual(len(first.hits), 1)
                self.assertEqual(len(second.hits), 1)
                self.assertIsNone(second.next_cursor)
                evidence = {hit.item_id: hit.evidence for hit in first.hits + second.hits}
                self.assertEqual(set(evidence), {note.pk, extracted.pk})
                note_evidence, = evidence[note.pk]
                self.assertEqual(note_evidence.source, "item")
                self.assertIn("-12,7 mm", note_evidence.snippet)
                derived_evidence, = evidence[extracted.pk]
                self.assertEqual(derived_evidence.source, "derived_content")
                self.assertIn("−12,7 mm", derived_evidence.snippet)
                self.assertEqual(derived_evidence.locator, {"page": 17})
                self.assertEqual(derived_evidence.provenance["derived_content_id"], content.pk)
