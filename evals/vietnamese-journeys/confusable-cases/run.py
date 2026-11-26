"""Measure initial and expanded Vietnamese search on an isolated QA database."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from evaluate import fingerprint, read, unique, write
from scenario_matrix import MATRIX_FILES, judge_matrix, load_matrix, seed_search_cases


def validate(fixture):
    items = fixture["items"]
    cases = fixture["cases"]
    unique([item["id"] for item in items], "item ID")
    unique([case["id"] for case in cases], "case ID")
    unique([case["query"].strip().casefold() for case in cases], "query")
    ids = {item["id"] for item in items}
    for case in cases:
        unique(case["accept"], "acceptable result ID")
        if not set(case["accept"]) <= ids:
            raise ValueError(f"Unknown result ID at {case['id']}")


def measure(repo, fixture):
    database = os.environ.get("POSTGRES_DB")
    if (database != "kt_eval_edge_pairs"
            or os.environ.get("KT_EVAL_ALLOW_DISPOSABLE") != "1"
            or os.environ.get("POSTGRES_HOST") not in {"localhost", "127.0.0.1", "::1"}):
        raise RuntimeError("Use loopback kt_eval_edge_pairs with KT_EVAL_ALLOW_DISPOSABLE=1")

    sys.path.insert(0, str(repo / "apps/backend"))
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
    import django

    django.setup()
    from catalog.models import Item
    from django.contrib.auth import get_user_model
    from django.db import connection, transaction
    from search.services import SearchService

    if connection.vendor != "postgresql":
        raise RuntimeError("PostgreSQL required")
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database()")
        if cursor.fetchone()[0] != database:
            raise RuntimeError("Unexpected PostgreSQL database")

    users = get_user_model().objects
    with transaction.atomic():
        if users.exists() or Item.objects.exists():
            raise RuntimeError("Use a migrated empty evaluation database")
        labels, filters_by_case = seed_search_cases(fixture)
        service = SearchService()
        rows = []
        for case in fixture["cases"]:
            filters = filters_by_case[case["id"]]
            page = service.search(filters, case["query"], limit=5)
            offered = bool(getattr(page, "can_expand", False))
            follow = service.search(filters, case["query"], limit=5, expand=True) if offered else None
            rows.append({
                "id": case["id"],
                "kind": case["kind"],
                "accept": case["accept"],
                "initial": [labels[hit.item_id] for hit in page.hits],
                "offered": offered,
                "expanded": [labels[hit.item_id] for hit in follow.hits] if offered else None,
            })
        transaction.set_rollback(True)
    if users.exists() or Item.objects.exists():
        raise RuntimeError("Unexpected rows after evaluation rollback")
    return rows


def summarize(rows, follow_suggestions):
    positives = [row for row in rows if row["accept"]]
    negatives = [row for row in rows if not row["accept"]]

    def visible(row):
        return row["expanded"] if follow_suggestions and row["offered"] else row["initial"]

    return {
        "positives": len(positives),
        "top1_acceptable": sum(bool(set(visible(row)[:1]) & set(row["accept"])) for row in positives),
        "top5_any_acceptable": sum(bool(set(visible(row)) & set(row["accept"])) for row in positives),
        "top5_all_acceptable": sum(set(row["accept"]) <= set(visible(row)) for row in positives),
        "negatives": len(negatives),
        "negatives_with_hits": sum(bool(visible(row)) for row in negatives),
        "negative_hits_total": sum(len(visible(row)) for row in negatives),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=HERE.parents[2])
    parser.add_argument("--matrix", action="store_true", help="Measure all three scenario suites in one shared corpus")
    parser.add_argument("--validate-only", action="store_true", help="Check fixtures without opening a database")
    parser.add_argument("--require-all", action="store_true", help="Exit nonzero if either mode misses any matrix case")
    parser.add_argument("--expected-source", help="Commit whose backend is being measured")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.require_all and (not args.matrix or args.validate_only):
        parser.error("--require-all applies to a live --matrix run")
    if not args.validate_only and (not args.expected_source or not args.report):
        parser.error("a live run requires --expected-source and --report")
    fixture_file = HERE / "fixture.json"
    fixture = load_matrix() if args.matrix else read(fixture_file)
    validate(fixture)
    if args.validate_only:
        print(f"Validated {len(fixture['cases'])} cases and {len(fixture['items'])} notes.")
        return
    repo = args.repo.resolve()

    def git(*arguments):
        return subprocess.check_output(["git", "-C", str(repo), *arguments], text=True).strip()

    source = git("rev-parse", args.expected_source)
    backend_tree = git("rev-parse", f"{source}:apps/backend")
    if git("rev-parse", "HEAD:apps/backend") != backend_tree or git("status", "--porcelain", "--", "apps/backend"):
        raise RuntimeError("Checked-out backend differs from the requested source")
    if args.matrix:
        directory = MATRIX_FILES[0].parent
        freeze = ["git", "-C", str(directory)]
        if subprocess.check_output([*freeze, "status", "--porcelain", "--", *(p.name for p in MATRIX_FILES)]).strip():
            raise RuntimeError("Commit all matrix fixtures before measuring")
        fixture_commit = subprocess.check_output([*freeze, "rev-parse", "HEAD"], text=True).strip()
    rows = measure(repo, fixture)
    report = {
        "tested_source": source,
        "backend_tree": backend_tree,
        "runner_sha256": fingerprint(Path(__file__)),
        "scenario_module_sha256": fingerprint(HERE.parent / "scenario_matrix.py"),
        "evaluation_module_sha256": fingerprint(HERE.parent / "evaluate.py"),
        "notes": len(fixture["items"]),
        "initial": summarize(rows, follow_suggestions=False),
        "with_suggestions": summarize(rows, follow_suggestions=True),
        "suggestions_offered": sum(row["offered"] for row in rows),
        "negative_suggestions_offered": sum(row["offered"] for row in rows if not row["accept"]),
        "negative_expanded_hits_total": sum(len(row["expanded"] or []) for row in rows if not row["accept"]),
        "cases": rows,
    }
    if args.matrix:
        report["fixture_commit"] = fixture_commit
        report["fixture_sha256"] = {p.name: fingerprint(p) for p in MATRIX_FILES}
        report["by_suite"] = judge_matrix(rows, fixture)
    else:
        report["fixture_sha256"] = fingerprint(fixture_file)
    write(args.report, report, exclusive=True)
    if args.matrix:
        totals = report["by_suite"]["all"]
        print(totals)
        if any(row[mode]["out_of_scope"] for row in rows for mode in ("initial_verdict", "with_suggestions_verdict")):
            raise SystemExit("Report written: a result fell outside its search scope")
        if args.require_all and min(totals["initial_pass"], totals["with_suggestions_pass"]) < totals["cases"]:
            raise SystemExit("Report written: at least one case missed its declared expectation")


if __name__ == "__main__":
    main()
