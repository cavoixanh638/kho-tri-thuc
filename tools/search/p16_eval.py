#!/usr/bin/env python3
"""P16 Vietnamese search evaluation. Never connects to production by default.

Offline: python tools/search/p16_eval.py --validate
Live:    P16_ALLOW_TEST_DB=1 python apps/backend/manage.py shell -c \
            "exec(open('tools/search/p16_eval.py',encoding='utf-8').read()); run_live()"
Run live from the repository root. Live mode rolls back all fixture writes.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import time
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "evals/parallel/p16-search/corpus.json"
CATEGORIES = {"title", "unaccented", "nfd_upper", "note", "derived", "capture",
              "topic_multi", "topic_excluded", "project_filter", "tag_filter",
              "tag_excluded", "cross_owner_filter", "owner_private", "deleted",
              "duplicate", "identifier", "typo", "literal_negative",
              "negative_provenance", "semantic"}


def load_corpus():
    return json.loads(CORPUS.read_text(encoding="utf-8"))


def validate(data):
    errors = []
    items = data.get("items", [])
    queries = data.get("queries", [])
    by_id = {item["id"]: item for item in items}
    if len(by_id) != len(items):
        errors.append("duplicate fixture item ID")
    if not 50 <= len(queries) <= 100:
        errors.append("query count outside 50..100")
    if len({q["id"] for q in queries}) != len(queries):
        errors.append("duplicate query ID")
    categories = Counter(q.get("category") for q in queries)
    for category in categories:
        if category not in CATEGORIES:
            errors.append("unknown category " + str(category))
    for q in queries:
        if not q.get("query") or not q.get("owner"):
            errors.append(q["id"] + ": missing query/owner")
        if len(q.get("gold", [])) != len(set(q.get("gold", []))):
            errors.append(q["id"] + ": repeated gold")
        for key in q["gold"]:
            if key not in by_id:
                errors.append(q["id"] + ": unknown gold " + key)
            elif by_id[key]["owner"] != q["owner"] or by_id[key].get("deleted"):
                errors.append(q["id"] + ": non-visible gold " + key)
        for kind, group in q.get("filters", {}).items():
            if kind not in ("topic", "project", "tag"):
                errors.append(q["id"] + ": unknown filter " + kind)
            if group.get("owner") not in data["owners"] or not group.get("name"):
                errors.append(q["id"] + ": bad filter reference")
        if q.get("expected_source") not in (None, "item", "derived_content", "capture_event"):
            errors.append(q["id"] + ": invalid source")
    if set(data["owners"]) != {"A", "B"}:
        errors.append("expected exactly two owners A and B")
    if any(item["owner"] not in data["owners"] for item in items):
        errors.append("unknown item owner")
    if not any(q["category"] == "semantic" for q in queries):
        errors.append("missing declared semantic challenge queries")
    return errors, categories


def quantile95(samples_ms):
    if not samples_ms:
        return None
    ordered = sorted(samples_ms)
    return ordered[math.ceil(.95 * len(ordered)) - 1]


def analyze(data, returned, latency_ms, evidence_errors):
    by_id = {q["id"]: q for q in data["queries"]}
    positive = [q for q in data["queries"] if q["gold"]]
    negative = [q for q in data["queries"] if not q["gold"]]
    matched = 0
    total_gold = sum(len(q["gold"]) for q in positive)
    total_returned = 0
    missing = {}
    negative_violations = {}
    per_category = {}
    for q in data["queries"]:
        qid = q["id"]
        row = returned[qid][:5]
        found = set(row)
        expected = set(q["gold"])
        if expected:
            matched += len(found & expected)
            total_returned += len(row)
            if expected - found:
                missing[qid] = sorted(expected - found)
        elif row:
            negative_violations[qid] = row
    for category in sorted({q["category"] for q in data["queries"]}):
        qs = [q for q in positive if q["category"] == category]
        denominator = sum(len(q["gold"]) for q in qs)
        if denominator:
            per_category[category] = {
                "positive_queries": len(qs),
                "recall_at_5": sum(len(set(q["gold"]) & set(returned[q["id"]][:5])) for q in qs) / denominator,
                "precision_at_5": sum(len(set(q["gold"]) & set(returned[q["id"]][:5])) for q in qs) /
                                  sum(len(returned[q["id"]][:5]) for q in qs)
                                  if any(returned[q["id"]][:5] for q in qs) else None,
            }
    return {
        "status": "MEASURED_SYNTHETIC_PG" if latency_ms else "NOT_RUN",
        "query_count": len(data["queries"]),
        "positive_queries": len(positive),
        "negative_queries": len(negative),
        "recall_at_5": matched / total_gold if total_gold else None,
        "precision_at_5": matched / total_returned if total_returned else None,
        "recall_formula": "sum(|top5(q) intersection gold(q)|)/sum(|gold(q)|), positive gold only",
        "precision_formula": "sum(|top5(q) intersection gold(q)|)/sum(|top5(q)|), positive gold only",
        "negative_violations": negative_violations,
        "missing_gold": missing,
        "evidence_errors": evidence_errors,
        "p95_ms": quantile95(latency_ms),
        "latency_count": len(latency_ms),
        "category_metrics": per_category,
        "no_leak": not any(qid in negative_violations for qid in
                          ("F09", "F11", "F12", "F07", "X05")),
        "limitations": [
            "Synthetic author-defined gold is not independent human relevance judgment.",
            "Semantic examples are challenges, not a requirement for current lexical FTS.",
            "P95 measures warm local Service.search calls only, not network/UI or cold-cache.",
            "No real-world corpus, Drive readback, or production data used."
        ],
    }


def run_live(out=None):
    if os.getenv("P16_ALLOW_TEST_DB") != "1":
        raise RuntimeError("Live evaluation requires P16_ALLOW_TEST_DB=1 and an isolated disposable PostgreSQL test DB")
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.db import connection, transaction
    from django.utils import timezone
    from catalog.models import Item, ItemTopic, ItemProject, ItemTag, Topic, Project, Tag, RelatedItem
    from processing.models import DerivedContent
    from ingestion.models import CaptureEvent
    from catalog.models import Source
    from search.services import SearchService, SearchFilters

    db_name = settings.DATABASES["default"]["NAME"]
    if not (db_name.startswith("test_") or db_name.startswith("p16_")):
        raise RuntimeError("Refusing live evaluation outside test_*/p16_* database")
    if connection.vendor != "postgresql":
        raise RuntimeError("PostgreSQL required: SQLite result is not valid")
    data = load_corpus()
    problems, _ = validate(data)
    if problems:
        raise ValueError("; ".join(problems))

    with transaction.atomic():
        user_model = get_user_model()
        owners = {name: user_model.objects.create_user(username="p16-" + name.lower() + "-" + os.urandom(4).hex()) for name in data["owners"]}
        groups = {}
        for typ, model in (("topic", Topic), ("project", Project), ("tag", Tag)):
            for name in data["owners"]:
                needed = set()
                for item in data["items"]:
                    if item["owner"] == name:
                        needed.update(item.get({"topic": "topics", "project": "projects", "tag": "tags"}[typ], []))
                needed.update(group["name"] for q in data["queries"] for key, group in q.get("filters", {}).items() if key == typ and group["owner"] == name)
                for label in needed:
                    groups[typ, name, label] = model.objects.create(owner=owners[name], name=label)
        db_items = {}
        for item in data["items"]:
            kwargs = {"owner": owners[item["owner"]], "kind": item.get("kind", "text"),
                      "title": unicodedata.normalize("NFD", item["title"]) if item.get("title_form") == "NFD" else item["title"],
                      "description": item.get("description", ""), "note": item.get("note", "")}
            if item.get("deleted"):
                kwargs["deleted_at"] = timezone.now()
            entry = Item.objects.create(**kwargs)
            db_items[item["id"]] = entry
            for typ, plural, assignment in (("topic", "topics", ItemTopic), ("project", "projects", ItemProject), ("tag", "tags", ItemTag)):
                for label in item.get(plural, []):
                    assignment.objects.create(item=entry, **{typ: groups[typ, item["owner"], label]})
            for part in item.get("derived", []):
                DerivedContent.objects.create(item=entry, kind=part["kind"], text=part["text"],
                    status=part.get("status", "active"), source_locator=part.get("locator", {}),
                    processor="p16-fixture", processor_version="1", input_hash="e" * 64)
            for cap in item.get("captures", []):
                CaptureEvent.objects.create(item=entry, owner=owners[item["owner"]],
                    raw_kind=cap["raw_kind"], raw_text=cap["raw_text"], original_url=cap["original_url"])
            for source in item.get("sources", []):
                Source.objects.create(item=entry, original_url="https://example.invalid/fixture",
                    canonical_url="https://example.invalid/fixture", identity_hash="f"*64, metadata=source["metadata"])
        for related in data.get("related", []):
            left, right = db_items[related["a"]], db_items[related["b"]]
            if left.pk > right.pk:
                left, right = right, left
            RelatedItem.objects.create(item_a=left,item_b=right,reason=related["reason"],
                method_version="p16", source_version="synthetic")
        reverse = {str(value.pk): key for key, value in db_items.items()}
        returned, latency, provenance_errors = {}, [], []
        service = SearchService()
        for q in data["queries"]:
            opts = {"owner_id": owners[q["owner"]].pk}
            for key, group in q.get("filters", {}).items():
                opts[key + "_id"] = groups[key, group["owner"], group["name"]].pk
            t0 = time.perf_counter_ns()
            page = service.search(SearchFilters(**opts), q["query"], limit=5)
            latency.append((time.perf_counter_ns() - t0) / 1e6)
            returned[q["id"]] = [reverse.get(str(hit.item_id), "UNEXPECTED:" + str(hit.item_id)) for hit in page.hits]
            for hit in page.hits:
                if str(hit.item_id) not in reverse:
                    provenance_errors.append(q["id"] + ": unrecognized Item UUID")
                else:
                    record = next((i for i in data["items"] if i["id"] == reverse[str(hit.item_id)]), None)
                    if record["owner"] != q["owner"] or record.get("deleted"):
                        provenance_errors.append(q["id"] + ": owner/deleted leak")
                for evidence in hit.evidence:
                    if evidence.source == "derived_content":
                        pk = evidence.provenance.get("derived_content_id")
                        if not pk or not DerivedContent.objects.filter(pk=pk,item_id=hit.item_id,status="active").exists():
                            provenance_errors.append(q["id"] + ": invalid derived attribution")
                        if evidence.locator is None:
                            provenance_errors.append(q["id"] + ": missing derived locator")
                    elif evidence.source == "capture_event":
                        pk = evidence.provenance.get("capture_event_id")
                        if not pk or not CaptureEvent.objects.filter(pk=pk,item_id=hit.item_id,owner=owners[q["owner"]],raw_kind="link").exists():
                            provenance_errors.append(q["id"] + ": invalid capture attribution")
                    elif evidence.source == "item":
                        if evidence.provenance:
                            provenance_errors.append(q["id"] + ": item evidence fabricated provenance")
                    else:
                        provenance_errors.append(q["id"] + ": unexpected evidence type " + str(evidence.source))
            if q.get("expected_source") and q["gold"]:
                for gold_key in q["gold"]:
                    target = next((hit for hit in page.hits if reverse.get(str(hit.item_id)) == gold_key), None)
                    if target and q["expected_source"] not in {e.source for e in target.evidence}:
                        provenance_errors.append(q["id"] + ": missing expected " + q["expected_source"])
        report = analyze(data, returned, latency, provenance_errors)
        report["db_backend"] = connection.vendor
        report["test_database"] = db_name
        report["item_count"] = len(db_items)
        report["p95_scope"] = "single warm in-process SearchService.search call; 86 sequential samples"
        report["fixture_transaction"] = "ROLLBACK"
        transaction.set_rollback(True)
    result = json.dumps(report, ensure_ascii=False, indent=2)
    if out:
        Path(out).write_text(result + "\n", encoding="utf-8")
    print(result)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true", help="Validate corpus and report live NOT_RUN")
    args = parser.parse_args()
    corpus = load_corpus()
    problems, counts = validate(corpus)
    status = "FAIL" if problems else "PASS"
    print(json.dumps({"offline_validation": status, "queries": len(corpus["queries"]),
                      "items": len(corpus["items"]), "categories": counts,
                      "errors": problems, "live_pg": "NOT_RUN",
                      "p95_ms": None, "recall_at_5": None, "precision_at_5": None},
                     ensure_ascii=False, indent=2))
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
