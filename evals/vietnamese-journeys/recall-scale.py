"""Measure a checkout's normal SearchService on the existing, synthetic P08/J9 scale DB."""

import argparse
import json
import math
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path


CASES = {
    "exact_id": "KTJ9TERM05678",
    "common_phrase": "kiểm thử phân trang",
    "remembered_with_id": "tôi nhớ bài KTJ9TERM05678 nói về cách phân trang",
    "common_near_miss": "hướng dẫn phục hồi lịch uống thuốc sau phẫu thuật",
    "unrelated": "cánh diều tre trong mùa gió chướng",
    "foreign_id": "KTJ9PRIVATEOTHEROWNER",
}
OWNER = "p08-j9-scale-fixture"


def run_git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def summarize_plan(cursor, sql, params):
    cursor.execute("EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, FORMAT JSON) " + sql, params)
    result = cursor.fetchone()[0]
    plan = json.loads(result)[0] if isinstance(result, str) else result[0]
    root = plan["Plan"]
    pending = [root]
    indexes = set()
    item_seq_rows = 0
    while pending:
        node = pending.pop()
        pending.extend(node.get("Plans", []))
        if not node["Actual Loops"]:
            continue
        if node.get("Index Name"):
            indexes.add(node["Index Name"])
        if node.get("Relation Name") == "catalog_item" and node["Node Type"] == "Seq Scan":
            item_seq_rows += node["Actual Loops"] * (node["Actual Rows"] + node.get("Rows Removed by Filter", 0))
    return {
        "execution_ms": round(plan["Execution Time"], 2),
        "item_seq_rows_examined": item_seq_rows,
        "indexes_used": sorted(indexes),
        "shared_blocks_hit": root.get("Shared Hit Blocks", 0),
        "shared_blocks_read": root.get("Shared Read Blocks", 0),
    }


def measure(repo, samples):
    sys.path.insert(0, str(repo / "apps/backend"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    django.setup()
    from django.contrib.auth import get_user_model
    from django.db import connection, transaction
    from catalog.models import Item, Topic
    from search.services import SearchFilters, SearchService

    db = connection.settings_dict
    if (db["HOST"] != "127.0.0.1" or str(db["PORT"]) != "56325" or db["USER"] != "kt_qa"
            or db["NAME"] not in {"kt_p08_scale", "kt_p08_scale_restored"}):
        raise ValueError("Select the loopback P08/J9 Windows QA database and role.")
    results = {}
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        cursor.execute("SET LOCAL statement_timeout = '15s'")
        cursor.execute("SELECT current_database(), current_user, current_setting('transaction_read_only')")
        if cursor.fetchone() != (db["NAME"], db["USER"], "on"):
            raise ValueError("Unexpected active database, role or transaction mode.")
        owner = get_user_model().objects.get(username=OWNER)
        visible = Item.objects.filter(owner=owner, deleted_at__isnull=True)
        if visible.count() != 10_000 or Topic.objects.filter(owner=owner).count() != 1000:
            raise ValueError("Expected the original 10k-item, 1k-topic P08/J9 fixture.")
        expected_id = visible.get(title__startswith=CASES["exact_id"] + " ").pk
        filters = SearchFilters(owner_id=owner.pk)
        service = SearchService()
        hits = {}
        timings = {name: [] for name in CASES}
        # One unmeasured warmup per query, then interleave measured queries in a static order.
        for i in range(samples + 1):
            for name, query in CASES.items():
                started = time.perf_counter_ns()
                page = service.search(filters, query, limit=5)
                elapsed = (time.perf_counter_ns() - started) / 1_000_000
                ids = tuple(hit.item_id for hit in page.hits)
                if i == 0:
                    hits[name] = ids
                    if visible.filter(pk__in=ids).count() != len(ids):
                        raise AssertionError("Result escaped the visible owner scope.")
                else:
                    if ids != hits[name]:
                        raise AssertionError(f"Inconsistent results for {name}.")
                    timings[name].append(elapsed)
        if hits["exact_id"] != (expected_id,) or hits["foreign_id"] or len(hits["common_phrase"]) != 5:
            raise AssertionError("Existing exact search, pagination or owner isolation regressed.")

        for name, query in CASES.items():
            statements = []

            def record(execute, sql, params, many, context):
                if sql.lstrip().upper().startswith(("SELECT", "WITH")):
                    statements.append((sql, params))
                return execute(sql, params, many, context)

            with connection.execute_wrapper(record):
                service.search(filters, query, limit=5)
            times = sorted(timings[name])
            ids = hits[name]
            results[name] = {
                "query": query,
                "results_returned": len(ids),
                "target_rank": ids.index(expected_id) + 1 if expected_id in ids else None,
                "median_ms": round(statistics.median(times), 2),
                "p95_ms": round(times[math.ceil(samples * 0.95) - 1], 2),
                "select_plans": [summarize_plan(cursor, sql, params) for sql, params in statements],
            }
    return {
        "application_sha": run_git(repo, "rev-parse", "HEAD"),
        "search_code_clean": not run_git(repo, "status", "--porcelain", "--", "apps/backend/search"),
        "database": db["NAME"],
        "owner_items": 10000,
        "owner_topics": 1000,
        "samples_per_case": samples,
        "scope": "Read-only, warm SearchService and local PostgreSQL; 10k repetitive synthetic notes, not a user library.",
        "cases": results,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--output", required=True, type=Path)
    options = parser.parse_args()
    if options.samples < 2:
        parser.error("Use at least two measured repetitions.")
    result = measure(options.app.resolve(), options.samples)
    options.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                              encoding="utf-8", newline="\n")
    for label, row in result["cases"].items():
        print(f"{label}  hits={row['results_returned']}  median={row['median_ms']} ms  p95={row['p95_ms']} ms")
