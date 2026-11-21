"""Offline P16 corpus and scoring contract tests; stdlib only."""
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "tools/search/p16_eval.py"
SPEC = importlib.util.spec_from_file_location("p16_eval", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class P16CorpusTests(unittest.TestCase):
    def setUp(self):
        self.data = MODULE.load_corpus()

    def test_gold_integrity_and_size(self):
        errors, categories = MODULE.validate(self.data)
        self.assertEqual(errors, [])
        self.assertGreaterEqual(len(self.data["queries"]), 50)
        self.assertLessEqual(len(self.data["queries"]), 100)
        self.assertEqual(len(self.data["owners"]), 2)
        self.assertGreaterEqual(len(categories), 10)

    def test_coverage_and_two_owners(self):
        kinds = {q["category"] for q in self.data["queries"]}
        for expected in ("unaccented", "nfd_upper", "derived", "capture", "duplicate",
                         "owner_private", "negative_provenance", "semantic", "topic_multi"):
            self.assertIn(expected, kinds)
        self.assertEqual({q["owner"] for q in self.data["queries"]}, {"A", "B"})

    def test_metrics_perfect_matches(self):
        returned = {q["id"]: q["gold"][:] for q in self.data["queries"]}
        result = MODULE.analyze(self.data, returned, [0.1] * len(returned), [])
        self.assertEqual(result["recall_at_5"], 1.0)
        self.assertEqual(result["precision_at_5"], 1.0)
        self.assertEqual(result["negative_violations"], {})
        self.assertEqual(result["p95_ms"], 0.1)

    def test_metrics_empty_results_and_zero_denominator(self):
        returned = {q["id"]: [] for q in self.data["queries"]}
        result = MODULE.analyze(self.data, returned, [], [])
        self.assertEqual(result["recall_at_5"], 0.0)
        self.assertIsNone(result["precision_at_5"])
        self.assertIsNone(result["p95_ms"])
        self.assertEqual(result["status"], "NOT_RUN")

    def test_negative_leak_and_false_attribution(self):
        returned = {q["id"]: [] for q in self.data["queries"]}
        returned["F09"] = ["b_secret"]
        result = MODULE.analyze(self.data, returned, [1.0], ["F09: owner/deleted leak"])
        self.assertFalse(result["no_leak"])
        self.assertEqual(result["negative_violations"]["F09"], ["b_secret"])
        self.assertTrue(result["evidence_errors"])

    def test_p95_nearest_rank(self):
        self.assertIsNone(MODULE.quantile95([]))
        self.assertEqual(MODULE.quantile95([float(x) for x in range(1, 21)]), 19.0)

    def test_golds_must_not_belong_to_other_owner(self):
        broken = json.loads(json.dumps(self.data))
        broken["queries"][0]["gold"] = ["b_secret"]
        errors, _ = MODULE.validate(broken)
        self.assertTrue(any("non-visible gold" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
