import re
from unittest import TestCase

from .identifiers import identifier_patterns
from .quantities import quantity_params


def python_pattern(pattern):
    # Use Python for the generated pattern shapes. The existing search tests
    # exercise PostgreSQL’s predicates and folding on indexed sources.
    return (pattern.replace("[[:alnum:]_/", r"[\w/")
            .replace("[[:alnum:]_", r"[\w")
            .replace("[[:alnum:]]", r"[^\W_]")
            .replace("[[:digit:]]", r"\d")
            .replace(r"\y", r"\b").replace(r"\m", r"\b").replace(r"\M", r"\b"))


class ValueFormatTests(TestCase):
    def assert_patterns(self, query, accepted, rejected):
        patterns = [*(identifier_patterns(query) or ()),
                    *(quantity_params(query)["quantity_required"] or ())]
        self.assertTrue(patterns)
        patterns = [re.compile(python_pattern(pattern)) for pattern in patterns]
        for passage in accepted:
            with self.subTest(query=query, passage=passage):
                self.assertTrue(all(pattern.search(passage) for pattern in patterns))
        for passage in rejected:
            with self.subTest(query=query, passage=passage):
                self.assertFalse(all(pattern.search(passage) for pattern in patterns))

    def test_explicit_measurements_share_unambiguous_decimal_marks(self):
        self.assert_patterns("độ vang 0.48 s", ("0,48 s", "0.48 s"), ("0,43 s", "0,48 m", "−0,48 s"))
        self.assert_patterns("dày 1,250 mm", ("1,250 mm",), ("1.250 mm", "1250 tờ", "250 mm"))
        self.assert_patterns("-2,4 mm", ("−2.4 mm",), ("2.4 mm", "+2.4 mm", "−2.4 cm"))
        self.assert_patterns("tủ 0.48 s phiên bản 2.4.10", ("0,48 s, 2.4.10",),
                             ("0,48 s, 2.4.1", "0,48 s, 2.4.10.1"))
        self.assert_patterns("phiên bản 2.4.2025", ("2.4.2025",), ("2025-04-02", "2.4.2025.1"))

    def test_grouping_is_bound_to_an_explicit_count_unit(self):
        self.assert_patterns("1250 tờ", ("1.250 tờ", "1250 tờ", "1.250 TỜ"),
                             ("1,250 tờ", "1250 mm", "1.250 hộp", "01.250 tờ"))
        self.assert_patterns("1.250 tờ", ("1250 tờ",), ("1,250 mm", "2.1250 tờ"))

    def test_calendar_dates_follow_day_month_year_and_keep_constraints(self):
        self.assert_patterns("đo 04/06/2025", ("Đo 2025-06-04", "4/6/2025", "4.6.2025."),
                             ("2025-04-06", "2025-06-05", "04/06/20250", "14/06/2025"))
        self.assert_patterns("29/02/2024 và 01/03/2024", ("2024-02-29, 2024-03-01",),
                             ("2024-02-29", "2024-02-29, 2024-01-03"))
        self.assertIsNone(quantity_params("29/02/2025")["quantity_required"])
        self.assertIsNotNone(identifier_patterns("29/02/2025"))

    def test_ranges_and_codes_preserve_complete_endpoints(self):
        self.assert_patterns("độ ẩm 30-80% RH", ("30–80% RH", "30 — 80% RH"),
                             ("30% đến 80%", "130–80% RH", "30–800% RH", "40–80% RH"))
        self.assert_patterns("lịch 09:00-11:30", ("09:00–11:30", "09:00 — 11:30."),
                             ("09:00 hoặc 11:30", "09:00–11:30:00", "09:00–11:31",
                              "19:00–11:30", "09:00\n— 11:30"))
        self.assert_patterns("mã AX-173 và kệ KL.3", ("AX‑173; KL.3.",), ("AX-173; KL.33", "TAX‑173; KL.3"))

    def test_competing_values_keep_their_role_clues(self):
        for query, target, competing, clue in (
            ("lượng mưa Mây Lam 04/06/2025", "mây lam 2025-06-04", "đã ký 2025-06-05", "mua"),
            ("mây lam bản 4.2.17", "đã sửa bản 4.2.17", "bản 4.2.1", "lam"),
            ("puly Đá Sương rộng 26,4 mm", "rộng 26.4 mm", "rộng 15 mm", "suong"),
            ("kệ Hạ Sa 283 hộp", "283 hộp", "220 hộp", "ha"),
            ("ổ rời 19 MB/s", "19 MB/s", "19 Mb/s", "roi"),
        ):
            with self.subTest(query=query):
                params = quantity_params(query)
                wanted = re.compile(python_pattern(params["quantity_target"]))
                family = re.compile(python_pattern(params["quantity_family"]))
                self.assertIn(clue, params["quantity_clues"])
                self.assertTrue(wanted.search(target))
                self.assertTrue(family.search(competing))
                self.assertFalse(wanted.search(competing))
