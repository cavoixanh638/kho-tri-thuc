import unittest

from judge import compare, summarize
from scenario_matrix import HERE, load_matrix, read


class PilotJudgeTests(unittest.TestCase):
    def test_saved_reports_match_frozen_case_judgments_and_counts(self):
        fixture = load_matrix()
        report = read(HERE / "scenario-matrix" / "results-windows.json")
        expected = {
            "initial": (71, (9, 24, 38), 46, 5, 6, 51),
            "with_suggestions": (92, (28, 25, 39), 70, 10, 14, 82),
        }
        for mode, (passed, suites, single, multi, negative, any_top5) in expected.items():
            with self.subTest(mode=mode):
                rankings = {
                    row["id"]: row["expanded"] if mode == "with_suggestions" and row["offered"]
                    else row["initial"]
                    for row in report["cases"]
                }
                result = summarize(fixture["cases"], fixture["items"], rankings)
                self.assertEqual(result["all"], {
                    "cases": 120,
                    "pass": passed,
                    "single_top1": {"count": single, "total": 81},
                    "multi_all": {"count": multi, "total": 13},
                    "negative_false_positive": {"count": negative, "total": 26},
                    "positive_top5_any": {"count": any_top5, "total": 94},
                    "out_of_scope_cases": 0,
                })
                for suite, suite_pass in zip(("language", "values", "scope"), suites):
                    self.assertEqual(result["by_suite"][suite]["cases"], 40)
                    self.assertEqual(result["by_suite"][suite]["pass"], suite_pass)
                for row in report["cases"]:
                    verdict = result["cases"][row["id"]]
                    saved = row[f"{mode}_verdict"]
                    self.assertEqual({key: verdict[key] for key in saved}, saved)
                if mode == "with_suggestions":
                    late_hits = {
                        case_id: verdict["acceptable_ranks"]
                        for case_id, verdict in result["cases"].items()
                        if verdict["single_top1"] is False and verdict["positive_top5_any"]
                    }
                    self.assertEqual(late_hits, {"L05": [3], "L16": [4]})

    def test_compare_tracks_scope_separately_from_relevance_and_pass_changes(self):
        cases = [
            {"id": "V", "suite": "values", "accept": ["a"]},
            {"id": "S", "suite": "scope", "accept": ["a", "b"]},
            {"id": "N", "suite": "scope", "accept": []},
        ]
        items = [{"id": "a"}, {"id": "b"}, {"id": "guest", "owner": "guest"}]
        baseline = {"V": ["b", "a"], "S": ["a", "b"], "N": ["a"]}
        candidate = {"V": ["a"], "S": ["a", "b", "guest"], "N": ["guest"]}
        scored = summarize(cases, items, candidate)
        self.assertEqual(scored["all"]["multi_all"], {"count": 1, "total": 1})
        self.assertEqual(scored["all"]["pass"], 1)
        self.assertEqual(scored["all"]["out_of_scope_cases"], 2)

        changes = compare(cases, items, baseline, candidate)
        self.assertEqual(changes["by_suite"]["values"]["improved"], ["V"])
        self.assertEqual(changes["by_suite"]["scope"]["regressed"], ["S"])
        self.assertEqual(changes["new_out_of_scope"], ["S", "N"])
        self.assertEqual(compare(cases, items, candidate, baseline)["resolved_out_of_scope"], ["S", "N"])

    def test_invalid_rankings_do_not_count_as_empty_or_valid_results(self):
        cases = [{"id": "N", "suite": "scope", "accept": []}]
        items = [{"id": "a"}]
        for rankings in ({}, {"N": ["unknown"]}, {"N": ["a", "a"]}):
            with self.subTest(rankings=rankings), self.assertRaises(ValueError):
                summarize(cases, items, rankings)


if __name__ == "__main__":
    unittest.main()
