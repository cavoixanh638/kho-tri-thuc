"""P08/J9 / Issue #90: isolated 10k read-only query profile.

Attach a Django execute_wrapper around exactly three authenticated catalog pages
and three in-process SearchService calls. EXPLAIN the slowest SELECT from each.
Never store SQL text, row bodies, credentials or identifiable source URLs.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import time
from pathlib import Path

from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.test import Client

from catalog.models import Item, Topic
from search.services import SearchFilters, SearchService

DATABASE = "kt_p08_scale"
USERNAME = "p08-j9-scale-fixture"
OUT = Path("/tmp/p08-j9-scale/query-profile.json")


def require(ok, code):
    if not ok:
        raise AssertionError("P08_PROFILE_" + code)


def guard():
    require(os.environ.get("P08_J9_ISOLATED") == "YES", "EXPLICIT_ISOLATION_REQUIRED")
    require(os.environ.get("P08_J9_PROFILE") == "YES", "EXPLICIT_PROFILING_REQUIRED")
    require(connection.vendor == "postgresql", "POSTGRES_ONLY")
    require(connection.settings_dict.get("NAME") == DATABASE, "SOURCE_QA_DATABASE_ONLY")
    owner = get_user_model().objects.get(username=USERNAME)
    require(Item.objects.filter(owner=owner).count() == 10000, "EXPECTED_10K_ITEMS")
    require(Topic.objects.filter(owner=owner).count() == 1000, "EXPECTED_1K_TOPICS")
    return owner


def name_of(sql):
    """Return only coarse table/category, not interpolated content or SQL text."""
    expression = sql.casefold()
    if "catalog_item " in expression or "catalog_item\n" in expression:
        return "catalog_item"
    if "processing_derivedcontent" in expression:
        return "derived_content"
    if "catalog_source" in expression:
        return "source"
    if "storage_asset" in expression:
        return "asset"
    if "auth_user" in expression or "django_session" in expression:
        return "session"
    return "other"


def sql_digest(sql):
    return hashlib.sha256(sql.encode("utf-8", "replace")).hexdigest()[:16]


class Recorder:
    def __init__(self):
        self.rows = []

    def __call__(self, execute, sql, params, many, context):
        start = time.perf_counter_ns()
        try:
            return execute(sql, params, many, context)
        finally:
            elapsed = (time.perf_counter_ns() - start) / 1_000_000
            self.rows.append({
                "sql_sha256_prefix": sql_digest(sql),
                "category": name_of(sql),
                "query_type": sql.lstrip().split(maxsplit=1)[0].upper() if sql.strip() else "UNKNOWN",
                "duration_ms": round(elapsed, 3),
                # In memory only, NEVER serialize SQL/params.
                "_sql": sql, "_params": params, "_many": many,
            })


def summarize(recorder, wall_ms):
    readings = recorder.rows
    return {
        "wall_ms": round(wall_ms, 3),
        "sql_execution_ms": round(sum(row["duration_ms"] for row in readings), 3),
        "non_sql_or_fetch_ms": round(max(0.0, wall_ms - sum(row["duration_ms"] for row in readings)), 3),
        "queries": len(readings),
        "by_category": {
            category: {
                "count": sum(r["category"] == category for r in readings),
                "sql_execution_ms": round(sum(r["duration_ms"] for r in readings
                                               if r["category"] == category), 3),
            }
            for category in sorted({r["category"] for r in readings})
        },
        "slowest_query_samples": [
            {key: row[key] for key in ("sql_sha256_prefix", "category",
                                      "query_type", "duration_ms")}
            for row in sorted(readings, key=lambda x: -x["duration_ms"])[:4]
        ],
    }


def run_profile(action):
    recorder = Recorder()
    start = time.perf_counter_ns()
    with connection.execute_wrapper(recorder):
        value = action()
    elapsed = (time.perf_counter_ns() - start) / 1_000_000
    return value, recorder, summarize(recorder, elapsed)


def plan_summary(sql, params):
    if not sql.lstrip().upper().startswith(("SELECT", "WITH")):
        return {"status": "NOT_RUN", "reason": "NON_SELECT"}
    if "catalog_item" not in sql.casefold() and "processing_derivedcontent" not in sql.casefold():
        return {"status": "NOT_RUN", "reason": "NOT_CATALOG_SELECT"}
    # Run EXPLAIN ANALYZE with a hard SQL time limit and READ ONLY transaction.
    # This does execute SELECT on the synthetic database and is not a dry plan.
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL statement_timeout TO '7000ms'")
                cursor.execute("SET LOCAL default_transaction_read_only TO on")
                cursor.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + sql, params)
                result = cursor.fetchone()[0]
            transaction.set_rollback(True)
    except Exception:
        return {"status": "NOT_RUN", "reason": "EXPLAIN_FAILED_OR_TIMED_OUT"}
    if isinstance(result, str):
        result = json.loads(result)
    require(isinstance(result, list) and result and "Plan" in result[0], "EXPLAIN_INVALID")
    root = result[0]
    nodes = []

    def walk(node, depth=0):
        if len(nodes) >= 30:
            return
        nodes.append({
            "depth": depth,
            "node": str(node.get("Node Type", ""))[:80],
            "index": str(node.get("Index Name", ""))[:120] or None,
            "plan_rows": node.get("Plan Rows"),
            "actual_rows": node.get("Actual Rows"),
            "total_ms": node.get("Actual Total Time"),
            "loops": node.get("Actual Loops"),
            "shared_hit_blocks": node.get("Shared Hit Blocks", 0),
            "shared_read_blocks": node.get("Shared Read Blocks", 0),
            "temp_read_blocks": node.get("Temp Read Blocks", 0),
            "temp_written_blocks": node.get("Temp Written Blocks", 0),
        })
        for child in node.get("Plans", []):
            walk(child, depth+1)

    walk(root["Plan"])
    return {
        "status": "MEASURED_ISOLATED_POSTGRES",
        "planning_ms": round(root.get("Planning Time", 0), 3),
        "execution_ms": round(root.get("Execution Time", 0), 3),
        "node_count_recorded": len(nodes), "nodes": nodes,
    }


def measured_plan(recorder):
    selectable = [
        row for row in recorder.rows
        if row["query_type"] in ("SELECT", "WITH")
        and not row["_many"]
        and row["category"] in ("catalog_item", "derived_content")
    ]
    if not selectable:
        return {"status": "NOT_RUN", "reason": "NO_CATALOG_SELECT"}
    target = max(selectable, key=lambda x: x["duration_ms"])
    return {
        "sql_sha256_prefix": target["sql_sha256_prefix"],
        "category": target["category"],
        **plan_summary(target["_sql"], target["_params"]),
    }


def main():
    owner = guard()
    client = Client(HTTP_HOST="127.0.0.1")
    client.force_login(owner)
    result = {
        "schema_version": 1, "task": "Issue#90/P08_10K_SQL_PROFILE",
        "status": "MEASURED_SYNTHETIC_ONLY",
        "database": DATABASE, "expected_items": 10000, "expected_topics": 1000,
        "measurement_scope": "Warm Django in-process Client + SearchService on shared QA runner; not production network or real media",
        "samples": [], "plans": [],
    }
    for offset in (0, 5000, 9900):
        value, recorder, timing = run_profile(
            lambda offset=offset: client.get("/api/v1/items", data={
                "limit": 100, "offset": offset,
            })
        )
        require(value.status_code == 200, "CATALOG_HTTP_NOT_200")
        rows = value.json()["results"]
        require(len(rows) == 100 and len({r["item_id"] for r in rows}) == 100,
                "CATALOG_PAGE_INCOMPLETE")
        result["samples"].append({
            "kind": "catalog_http", "offset": offset, "items": len(rows), **timing
        })
        result["plans"].append({
            "kind": "catalog_http", "offset": offset,
            **measured_plan(recorder)
        })
    service = SearchService()
    for label, query in (
        ("exact_first", "KTJ9TERM00000"),
        ("exact_last", "KTJ9TERM09999"),
        ("common", "kiểm thử phân trang"),
    ):
        value, recorder, timing = run_profile(
            lambda query=query: service.search(SearchFilters(owner_id=owner.pk), query, limit=5)
        )
        require(len(value.hits) > 0, "SEARCH_EMPTY_" + label.upper())
        require(all(Item.objects.filter(pk=h.item_id, owner=owner).exists()
                    for h in value.hits), "SEARCH_OWNER_LEAK")
        result["samples"].append({
            "kind": "search_service", "query_label": label,
            "hits": len(value.hits), **timing
        })
        result["plans"].append({
            "kind": "search_service", "query_label": label,
            **measured_plan(recorder)
        })

    require(len(result["samples"]) == 6 and len(result["plans"]) == 6,
            "SAMPLE_REGISTRY_INCOMPLETE")
    require(all(row["queries"] >= 1 for row in result["samples"]),
            "NO_QUERIES_RECORDED")
    result["http_samples"] = 3
    result["search_samples"] = 3
    result["limitations"] = [
        "No speed target or regression verdict is asserted: this is diagnostic only.",
        "3 HTTP pages and 3 search queries cannot establish statistically stable p95.",
        "SQL execute time does not include result hydration and JSON serialization.",
        "EXPLAIN ANALYZE executes SELECT against synthetic QA, and buffers reflect shared CI resource contention.",
        "No raw SQL text, bound values, URLs, notes or credentials are stored.",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)+"\n",
                   encoding="utf-8")
    print(json.dumps({
        "status": result["status"], "samples": len(result["samples"]),
        "plans": len(result["plans"]),
        "sql_explained": sum(p["status"] == "MEASURED_ISOLATED_POSTGRES"
                             for p in result["plans"]),
        "http_wall_ms": [s["wall_ms"] for s in result["samples"] if s["kind"] == "catalog_http"],
        "search_wall_ms": [s["wall_ms"] for s in result["samples"] if s["kind"] == "search_service"],
    }))


main()
