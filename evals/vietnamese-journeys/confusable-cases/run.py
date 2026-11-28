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


def service_page(page, labels):
    return {
        "hits": [labels[hit.item_id] for hit in page.hits],
        "can_expand": page.can_expand,
        "ranking": getattr(page, "ranking", None),
    }


def api_page(client, case, filters, labels, expand):
    params = {
        f"{name}_id": value for name in ("topic", "project", "tag")
        if (value := getattr(filters, f"{name}_id")) is not None
    }
    if filters.exclude_item_id is not None:
        params["exclude_item_id"] = str(filters.exclude_item_id)
    if expand:
        params["expand"] = "true"
    response = client.get("/api/v1/search", {"q": case["query"], "limit": 5, **params})
    if response.status_code != 200:
        raise RuntimeError(f"Search API returned HTTP {response.status_code} for {case['id']} (expand={expand})")
    page = response.json()
    return {
        "hits": [labels[hit["item_id"]] for hit in page["results"]],
        "can_expand": page.get("can_expand"),
        "ranking": page.get("ranking"),
    }


def measure(repo, fixture, *, check_bge=False):
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
    from django.test import Client
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
        clients = {}
        api_labels = {str(pk): label for pk, label in labels.items()}
        for case in fixture["cases"]:
            filters = filters_by_case[case["id"]]
            page = service.search(filters, case["query"], limit=5)
            offered = bool(getattr(page, "can_expand", False))
            follow = service.search(filters, case["query"], limit=5, expand=True) if offered else None
            row = {
                "id": case["id"],
                "kind": case["kind"],
                "accept": case["accept"],
                "initial": [labels[hit.item_id] for hit in page.hits],
                "offered": offered,
                "expanded": [labels[hit.item_id] for hit in follow.hits] if offered else None,
            }
            if check_bge:
                row["service"] = {"initial": service_page(page, labels), "expanded": service_page(follow, labels) if offered else None}
                if filters.owner_id not in clients:
                    client = Client(SERVER_NAME="localhost")
                    client.force_login(users.get(pk=filters.owner_id))
                    clients[filters.owner_id] = client
                client = clients[filters.owner_id]
                api_initial = api_page(client, case, filters, api_labels, expand=False)
                api_expanded = (
                    api_page(client, case, filters, api_labels, expand=True)
                    if api_initial["can_expand"] is True else None
                )
                row["api"] = {"initial": api_initial, "expanded": api_expanded}
            rows.append(row)
        transaction.set_rollback(True)
    if users.exists() or Item.objects.exists():
        raise RuntimeError("Unexpected rows after evaluation rollback")
    return rows


def check_bge_report(report, baseline):
    errors = []
    for key in ("fixture_sha256", "scenario_module_sha256", "evaluation_module_sha256", "notes"):
        if key not in baseline or report[key] != baseline[key]:
            errors.append(f"Frozen baseline mismatch: {key}")
    rows = report["cases"]
    frozen = baseline.get("cases", [])
    if [row["id"] for row in rows] != [row["id"] for row in frozen]:
        errors.append("Frozen baseline case IDs or ordering differ")
    if errors:
        return {"errors": errors}

    counts = {
        path: {"initial_requests": len(rows), "expanded_requests": 0, "eligible": 0, "bge": 0, "fallback": 0}
        for path in ("service", "api")
    }
    for row, old in zip(rows, frozen, strict=True):
        case_id = row["id"]

        def expect(condition, detail):
            if not condition:
                errors.append(f"{case_id}: {detail}")

        for field in ("kind", "accept", "suite"):
            expect(row[field] == old.get(field), f"frozen case {field} changed")
        service = row["service"]
        expect(service["initial"]["hits"] == old.get("initial"), "initial lexical order changed")
        expect(service["initial"]["can_expand"] is old.get("offered"), "initial can_expand changed")
        if old["offered"] and service["expanded"] is not None:
            hits = service["expanded"]["hits"]
            frozen_hits = old["expanded"]
            window = min(5, len(frozen_hits))
            expect(sorted(hits[:window]) == sorted(frozen_hits[:window]), "expanded shortlist changed")
            expect(hits[window:] == frozen_hits[window:], "expanded results after shortlist changed")
            if not old["accept"]:
                expect(not hits, "expanded negative query returned hits")
        expect(row["api"] == service, "authenticated API and service differ")

        size = len(old["expanded"] or [])
        for path, totals in counts.items():
            pages = row[path]
            expect(pages["initial"]["ranking"] == "lexical", f"{path} initial ranking must be lexical")
            expanded = pages["expanded"]
            expect((expanded is not None) == old["offered"], f"{path} expansion followed a different case set")
            eligible = old["offered"] and size >= 2
            totals["eligible"] += eligible
            totals["fallback"] += eligible and (expanded is None or expanded["ranking"] != "bge")
            if expanded is None:
                continue
            totals["expanded_requests"] += 1
            expect(expanded["can_expand"] is False, f"{path} expanded can_expand must be false")
            ranking = expanded["ranking"]
            totals["bge"] += ranking == "bge"
            expected = "bge" if eligible else "lexical"
            expect(ranking == expected, f"{path} expanded ranking {ranking!r}; expected {expected} for {size} candidates")
    for path, totals in counts.items():
        if not totals["eligible"]:
            errors.append(f"No eligible {path} BGE calls measured")
    return {**counts, "errors": errors}


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
    parser.add_argument(
        "--check-bge-against", type=Path, metavar="LEXICAL_REPORT",
        help="Require real BGE ranking on eligible service and authenticated API requests",
    )
    args = parser.parse_args()
    if args.check_bge_against and (not args.matrix or args.validate_only):
        parser.error("--check-bge-against applies to a live --matrix run")
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
    baseline = read(args.check_bge_against) if args.check_bge_against else None
    rows = measure(repo, fixture, check_bge=args.check_bge_against is not None)
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
    if args.check_bge_against:
        report["bge_check"] = check_bge_report(report, baseline)
        report["bge_check"]["baseline_sha256"] = fingerprint(args.check_bge_against)
        report["bge_check"]["baseline_source"] = baseline.get("tested_source")
    write(args.report, report, exclusive=True)
    if args.check_bge_against:
        print(report["bge_check"])
        if report["bge_check"]["errors"]:
            raise SystemExit("Report written: BGE verification failed")
    if args.matrix:
        totals = report["by_suite"]["all"]
        print(totals)
        if any(row[mode]["out_of_scope"] for row in rows for mode in ("initial_verdict", "with_suggestions_verdict")):
            raise SystemExit("Report written: a result fell outside its search scope")
        if args.require_all and min(totals["initial_pass"], totals["with_suggestions_pass"]) < totals["cases"]:
            raise SystemExit("Report written: at least one case missed its declared expectation")


if __name__ == "__main__":
    main()
