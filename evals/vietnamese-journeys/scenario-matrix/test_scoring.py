import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scenario_matrix import assess, judge_matrix


class MatrixScoringTests(unittest.TestCase):
    items = {
        "a": {"id": "a", "tags": ["đỏ"]},
        "b": {"id": "b", "tags": ["đỏ"]},
        "c": {"id": "c", "owner": "guest", "tags": ["đỏ"]},
        "d": {"id": "d", "trashed": True, "tags": ["đỏ"]},
        "e": {"id": "e", "tags": ["xanh"]},
    }

    def test_single_result_must_rank_first(self):
        self.assertFalse(assess(["b", "a"], {"accept": ["a"]}, self.items)["pass"])
        self.assertTrue(assess(["a", "b"], {"accept": ["a"]}, self.items)["pass"])

    def test_all_requested_results_must_be_present(self):
        case = {"accept": ["a", "b"]}
        self.assertFalse(assess(["b"], case, self.items)["pass"])
        self.assertTrue(assess(["b", "a"], case, self.items)["pass"])
        six = {key: {"id": key} for key in "abcdef"}
        self.assertFalse(assess(["a", "c", "d", "e", "f", "b"], case, six)["pass"])

    def test_negative_requires_an_empty_result(self):
        self.assertFalse(assess(["a"], {"accept": []}, self.items)["pass"])
        self.assertTrue(assess([], {"accept": []}, self.items)["pass"])

    def test_correct_first_result_cannot_hide_scope_errors(self):
        case = {"accept": ["a"], "filters": {"tag": "đỏ", "exclude": "b"}}
        verdict = assess(["a", "b", "c", "d", "e"], case, self.items)
        self.assertFalse(verdict["pass"])
        self.assertEqual(verdict["out_of_scope"], ["b", "c", "d", "e"])

    def test_offered_empty_expansion_is_scored_as_empty(self):
        case = {"id": "q", "suite": "scope", "accept": ["a"]}
        data = {"items": list(self.items.values()), "cases": [case]}
        rows = [{"id": "q", "initial": ["a"], "offered": True, "expanded": []}]
        result = judge_matrix(rows, data)
        self.assertEqual(result["all"], {"cases": 1, "initial_pass": 1, "with_suggestions_pass": 0})
        rows[0].update(offered=False, expanded=None)
        self.assertEqual(judge_matrix(rows, data)["all"]["with_suggestions_pass"], 1)


if __name__ == "__main__":
    unittest.main()
