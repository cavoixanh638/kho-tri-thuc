"""Score fixture rankings with summarize() and compare two runs with compare()."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scenario_matrix import assess


RATES = ("single_top1", "multi_all", "negative_false_positive", "positive_top5_any")


def _counts():
    return {
        "cases": 0,
        "pass": 0,
        **{key: {"count": 0, "total": 0} for key in RATES},
        "out_of_scope_cases": 0,
    }


def summarize(cases, items, rankings):
    """Return overall and suite counts, plus verdicts keyed by fixture case ID."""
    case_ids = {case["id"] for case in cases}
    if case_ids != rankings.keys():
        missing = sorted(case_ids - rankings.keys())
        extra = sorted(rankings.keys() - case_ids)
        raise ValueError(f"Ranking case IDs differ from fixture (missing={missing}, extra={extra})")
    item_by_id = {item["id"]: item for item in items}
    by_suite = {suite: _counts() for suite in sorted({case["suite"] for case in cases})}
    summary = {"all": _counts(), "by_suite": by_suite, "cases": {}}
    for case in cases:
        case_id = case["id"]
        result_ids = list(rankings[case_id])
        if len(result_ids) > 5 or len(set(result_ids)) != len(result_ids):
            raise ValueError(f"Expected up to five distinct ranked item IDs for {case_id}")
        unknown = set(result_ids) - item_by_id.keys()
        if unknown:
            raise ValueError(f"Unknown ranked item IDs for {case_id}: {sorted(unknown)}")

        expected = case["accept"]
        ranks = [rank for rank, item_id in enumerate(result_ids, start=1) if item_id in expected]
        checks = {
            "single_top1": 1 in ranks if len(expected) == 1 else None,
            "multi_all": len(ranks) == len(expected) if len(expected) > 1 else None,
            "negative_false_positive": bool(result_ids) if not expected else None,
            "positive_top5_any": bool(ranks) if expected else None,
        }
        verdict = assess(result_ids, case, item_by_id)
        summary["cases"][case_id] = {
            "suite": case["suite"],
            **verdict,
            **checks,
            "acceptable_ranks": ranks,
        }
        for group in (summary["all"], by_suite[case["suite"]]):
            group["cases"] += 1
            group["pass"] += verdict["pass"]
            group["out_of_scope_cases"] += bool(verdict["out_of_scope"])
            for key, hit in checks.items():
                if hit is not None:
                    group[key]["total"] += 1
                    group[key]["count"] += hit
    return summary


def compare(cases, items, baseline, candidate):
    """Return IDs of pass and scope transitions overall and per suite."""
    before = summarize(cases, items, baseline)
    after = summarize(cases, items, candidate)
    keys = ("improved", "regressed", "new_out_of_scope", "resolved_out_of_scope")
    changes = {key: [] for key in keys}
    changes["by_suite"] = {suite: {key: [] for key in keys} for suite in before["by_suite"]}
    for case_id, old in before["cases"].items():
        new = after["cases"][case_id]
        transitions = {
            "improved": not old["pass"] and new["pass"],
            "regressed": old["pass"] and not new["pass"],
            "new_out_of_scope": not old["out_of_scope"] and bool(new["out_of_scope"]),
            "resolved_out_of_scope": bool(old["out_of_scope"]) and not new["out_of_scope"],
        }
        for key, changed in transitions.items():
            if changed:
                changes[key].append(case_id)
                changes["by_suite"][old["suite"]][key].append(case_id)
    return changes
