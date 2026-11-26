"""Checks that the opt-in BGE report gate fails when its contract changes."""

from copy import deepcopy
from unittest import TestCase

from run import check_bge_report


class BgeReportTests(TestCase):
    def setUp(self):
        metadata = {
            "fixture_sha256": {"language.json": "fixture-hash"},
            "scenario_module_sha256": "scenario-hash",
            "evaluation_module_sha256": "evaluation-hash",
            "notes": 8,
        }
        case = {"id": "L01", "kind": "remembered", "suite": "language", "accept": ["b"]}
        self.baseline = {
            **metadata,
            "cases": [{**case, "initial": ["a"], "offered": True, "expanded": list("abcdefg")}],
        }
        pages = {
            "initial": {"hits": ["a"], "can_expand": True, "ranking": "lexical"},
            "expanded": {"hits": list("bacdefg"), "can_expand": False, "ranking": "bge"},
        }
        self.row = {**case, "service": pages, "api": deepcopy(pages)}
        self.report = {**metadata, "cases": [self.row]}

    def check(self):
        return check_bge_report(self.report, self.baseline)

    def test_accepts_same_shortlist_and_tail(self):
        result = self.check()
        self.assertEqual(result["errors"], [])
        for path in ("service", "api"):
            self.assertEqual(result[path], {
                "initial_requests": 1, "expanded_requests": 1, "eligible": 1, "bge": 1, "fallback": 0,
            })

    def test_identical_order_requires_bge_marker(self):
        for path in ("service", "api"):
            self.row[path]["expanded"]["hits"] = list("abcdefg")
        self.assertEqual(self.check()["errors"], [])
        self.row["api"]["expanded"]["ranking"] = "lexical"
        result = self.check()
        self.assertEqual(result["api"]["fallback"], 1)
        self.assertIn("L01: api expanded ranking 'lexical'; expected bge for 7 candidates", result["errors"])

    def test_rejects_changed_initial_order_shortlist_tail_or_button(self):
        self.row["service"]["initial"] = {"hits": ["b"], "can_expand": False, "ranking": "bge"}
        self.row["service"]["expanded"]["hits"] = list("bacxegf")
        result = self.check()
        self.assertIn("L01: initial lexical order changed", result["errors"])
        self.assertIn("L01: initial can_expand changed", result["errors"])
        self.assertIn("L01: service initial ranking must be lexical", result["errors"])
        self.assertIn("L01: expanded shortlist changed", result["errors"])
        self.assertIn("L01: expanded results after shortlist changed", result["errors"])

    def test_rejects_mismatched_fixture_or_case_ids(self):
        self.baseline["fixture_sha256"] = {}
        self.baseline["cases"][0]["id"] = "L02"
        self.assertEqual(self.check()["errors"], [
            "Frozen baseline mismatch: fixture_sha256",
            "Frozen baseline case IDs or ordering differ",
        ])

    def test_rejects_bge_for_one_hit(self):
        self.baseline["cases"][0]["expanded"] = ["a"]
        for path in ("service", "api"):
            self.row[path]["expanded"]["hits"] = ["a"]
        result = self.check()
        self.assertIn("L01: api expanded ranking 'bge'; expected lexical for 1 candidates", result["errors"])
        self.assertIn("No eligible service BGE calls measured", result["errors"])
