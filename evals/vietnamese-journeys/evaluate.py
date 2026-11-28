"""Measure actual organization jobs, owner-scoped search and a correction roundtrip."""

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path
from uuid import NAMESPACE_URL, uuid4, uuid5

HERE = Path(__file__).resolve().parent
SPLITS = ("development", "holdout")


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, data, exclusive=False):
    with path.open("x" if exclusive else "w", encoding="utf-8", newline="\n") as output:
        json.dump(data, output, ensure_ascii=False, indent=2)
        output.write("\n")


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique(values, label):
    if len(values) != len(set(values)) or any(not value.strip() for value in values):
        raise ValueError(f"Empty or duplicate {label}")


def validate_corpus(data):
    unique(data["topics"], "topic")
    unique([row["id"] for row in data["items"]], "item ID")
    unique([row["note"].strip().casefold() for row in data["items"]], "note body")
    if {row["split"] for row in data["items"]} != set(SPLITS):
        raise ValueError("Declare both development and holdout splits")
    if not all(row["title"].strip() for row in data["items"]):
        raise ValueError("Missing title")


def review_form(data, corpus_hash):
    return {
        "origin": "human_blind",
        "corpus_sha256": corpus_hash,
        "attest_before_results": False,
        "topics_available": data["topics"],
        "judgments": [
            {
                "id": row["id"], "title": row["title"], "note": row["note"],
                "reviewed": False, "topics": [], "query": "", "query_kind": "memory",
            }
            for row in data["items"]
        ],
        "negative_queries": [],
    }


def validate_labels(data, gold, corpus_hash):
    rows = gold["judgments"]
    unique([row["id"] for row in rows], "judgment ID")
    unique([row["query"].strip().casefold() for row in rows + gold["negative_queries"]], "query")
    if {row["id"] for row in rows} != {row["id"] for row in data["items"]}:
        raise ValueError("One judgment is required per item")
    for row in rows:
        unique(row["topics"], "assigned topic")
        if set(row["topics"]) - set(data["topics"]):
            raise ValueError(f"Unknown topic at {row['id']}")
        if row["query_kind"] not in {"literal", "memory", "unaccented"}:
            raise ValueError(f"Unknown query type at {row['id']}")
    if any(q["split"] not in SPLITS for q in gold["negative_queries"]):
        raise ValueError("Unknown split in negative queries")
    if gold["origin"] == "human_blind":
        if (gold.get("corpus_sha256") != corpus_hash
                or gold.get("attest_before_results") is not True
                or not all(row.get("reviewed") is True for row in rows)):
            raise ValueError("Complete the blind form and attest before viewing results")
    elif gold["origin"] != "model_authored_provisional":
        raise ValueError("Unknown gold provenance")


def ratio(n, d):
    return {"numerator": n, "denominator": d, "value": n / d if d else None}


def summarize(rows, negatives):
    correct = sum(len(set(r["expected"]) & set(r["actual"])) for r in rows)
    predicted = sum(len(r["actual"]) for r in rows)
    expected = sum(len(r["expected"]) for r in rows)
    eligible = [r for r in rows if r["expected"]]
    abstain = [r for r in rows if not r["expected"]]
    ms = sorted(r["service_ms"] for r in rows + negatives)
    return {
        "items": len(rows),
        "organization": {
            "assignment_precision": ratio(correct, predicted),
            "false_assignment_rate": ratio(predicted - correct, predicted),
            "expected_assignment_recall": ratio(correct, expected),
            "eligible_item_coverage": ratio(sum(bool(r["actual"]) for r in eligible), len(eligible)),
            "correct_abstentions": ratio(sum(not r["actual"] for r in abstain), len(abstain)),
            "items_requiring_any_correction": ratio(sum(r["expected"] != r["actual"] for r in rows), len(rows)),
        },
        "search": {
            "target_found_in_top5": ratio(sum(r["rank"] is not None for r in rows), len(rows)),
            "target_at_rank1": ratio(sum(r["rank"] == 1 for r in rows), len(rows)),
            "by_query_kind": {
                kind: ratio(sum(r["rank"] is not None for r in rows if r["kind"] == kind),
                            sum(r["kind"] == kind for r in rows))
                for kind in sorted({r["kind"] for r in rows})
            },
            "negative_queries_with_results": ratio(sum(bool(r["top5"]) for r in negatives), len(negatives)),
            "service_p95_ms": ms[math.ceil(.95 * len(ms)) - 1],
            "latency_samples": len(ms),
        },
    }


def measure(repo, data, gold, follow_suggestions=False):
    # Reject an unintended endpoint before Django initializes or any DB call runs.
    database = os.environ.get("POSTGRES_DB", "")
    if (os.environ.get("KT_EVAL_ALLOW_DISPOSABLE") != "1"
            or not database.startswith("kt_eval_")
            or os.environ.get("POSTGRES_HOST") not in {"localhost", "127.0.0.1", "::1"}):
        raise RuntimeError("Use an isolated loopback kt_eval_* DB and KT_EVAL_ALLOW_DISPOSABLE=1")
    sys.path.insert(0, str(repo / "apps/backend"))
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
    import django
    django.setup()
    from django.contrib.auth import get_user_model
    from django.db import connection, transaction
    from django.test import Client
    from catalog.models import Item, ItemTopic, Topic
    from catalog.organization_job import organize_item
    from jobs.models import Job
    from search.services import SearchFilters, SearchService

    if connection.vendor != "postgresql":
        raise RuntimeError("PostgreSQL required")
    labels = {row["id"]: row for row in gold["judgments"]}
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            if cursor.fetchone()[0] != database:
                raise RuntimeError("Unexpected PostgreSQL database")
        if get_user_model().objects.exists() or Item.objects.exists():
            raise RuntimeError("Use a migrated empty evaluation database")
        owner = get_user_model().objects.create_user(username="kt-eval-" + uuid4().hex)
        topics = {name: Topic.objects.create(owner=owner, name=name) for name in data["topics"]}
        items = {}
        for source in data["items"]:
            key = source["id"]
            items[key] = Item.objects.create(
                id=uuid5(NAMESPACE_URL, "urn:kt-eval-item:" + key),
                kind=Item.Kind.TEXT, owner=owner, title=source["title"], note=source["note"],
            )
        reverse = {item.pk: key for key, item in items.items()}
        jobs = {}
        for key, item in items.items():
            jobs[key] = Job.objects.create(item=item, kind="organize", idempotency_key=f"kt-eval:{item.pk}")
            organize_item(jobs[key])

        filters = SearchFilters(owner_id=owner.pk)
        service = SearchService()

        def top5(query, target):
            start = time.perf_counter()
            page = service.search(filters, query, limit=5)
            elapsed = (time.perf_counter() - start) * 1000
            found = [reverse[hit.item_id] for hit in page.hits]
            detail = {"default_top5": found, "expanded": False} if follow_suggestions else {}
            if follow_suggestions and target not in found and getattr(page, "can_expand", False):
                expanded = service.search(filters, query, limit=5, expand=True)
                found = [reverse[hit.item_id] for hit in expanded.hits]
                detail["expanded"] = True
            return {"top5": found, "service_ms": round(elapsed, 3), **detail}

        measured = []
        for source in data["items"]:
            key = source["id"]
            label = labels[key]
            actual = ItemTopic.objects.filter(item=items[key], origin="auto").values_list("topic__name", flat=True)
            result = top5(label["query"], key)
            found = result["top5"]
            measured.append({
                "id": key, "split": source["split"], "expected": sorted(label["topics"]),
                "actual": sorted(actual), "kind": label["query_kind"], **result,
                "rank": found.index(key) + 1 if key in found else None,
            })
        negatives = []
        for n, q in enumerate(gold["negative_queries"], 1):
            negatives.append({"id": f"N{n:02}", "split": q["split"], **top5(q["query"], None)})
        # Probe the actual PATCH path after collecting scores, then rerun the job.
        correction = {"status": "NOT_RUN_NO_MISSING_TOPIC"}
        for row in measured:
            missing = sorted(set(row["expected"]) - set(row["actual"]))
            if not missing:
                continue
            item, topic = items[row["id"]], topics[missing[0]]
            path = f"/api/v1/items/{item.pk}/organization"
            client = Client(HTTP_HOST="localhost")
            client.force_login(owner)
            res = client.patch(path, {"topic_ids": [str(topic.pk)]}, content_type="application/json")
            if res.status_code != 200:
                raise RuntimeError(f"Correction API failed: {res.status_code}")
            organize_item(jobs[row["id"]])
            check = client.get(path)
            if check.status_code != 200:
                raise RuntimeError(f"Reread API failed: {check.status_code}")
            persisted = any(
                str(group["id"]) == str(topic.pk) and group["user_pinned"] and group["origin"] == "user"
                for group in check.json()["topics"]
            )
            correction = {"status": "PASS" if persisted else "FAIL", "item_id": row["id"],
                          "action": "pin_missing_topic_then_reorganize_and_get", "persisted": persisted}
            break
        remove_wrong = {"status": "NOT_RUN_NO_FALSE_ASSIGNMENT"}
        for row in measured:
            wrong = sorted(set(row["actual"]) - set(row["expected"]))
            if not wrong:
                continue
            item, topic = items[row["id"]], topics[wrong[0]]
            client = Client(HTTP_HOST="localhost")
            client.force_login(owner)
            path = f"/api/v1/items/{item.pk}/placement"
            current = client.get(path).json()
            res = client.patch(path, {"action": "remove", "folder_id": topic.pk,
                                      "expected_version": current["structure_version"]},
                               content_type="application/json")
            if res.status_code != 200:
                raise RuntimeError(f"Organization PATCH failed: {res.status_code}")
            present_after_patch = any(g["folder_id"] == topic.pk for g in res.json()["memberships"])
            organize_item(jobs[row["id"]])
            check = client.get(path)
            if check.status_code != 200:
                raise RuntimeError(f"Organization GET failed: {check.status_code}")
            present_after_job = any(g["folder_id"] == topic.pk for g in check.json()["memberships"])
            remove_wrong = {
                "status": "FAIL" if present_after_patch or present_after_job else "PASS",
                "item_id": row["id"], "topic": wrong[0], "patch_http": res.status_code,
                "action": "explorer_remove_then_reorganize_and_get",
                "wrong_topic_present_after_patch": present_after_patch,
                "wrong_topic_present_after_job": present_after_job,
            }
            break
        transaction.set_rollback(True)
    report = {
        "by_split": {split: summarize([r for r in measured if r["split"] == split],
                                      [r for r in negatives if r["split"] == split]) for split in SPLITS},
        "overall": summarize(measured, negatives), "correction_probe": correction,
        "remove_wrong_auto_topic_probe": remove_wrong,
        "diagnostics": measured, "negative_queries": negatives,
    }
    if follow_suggestions:
        defaults = [{**r, "top5": r["default_top5"],
                     "rank": r["default_top5"].index(r["id"]) + 1 if r["id"] in r["default_top5"] else None}
                    for r in measured]
        plain_negatives = [{**r, "top5": r["default_top5"]} for r in negatives]
        report["before_expanding"] = summarize(defaults, plain_negatives)["search"]
        report["suggestion_policy"] = "Expand only when offered and target missing from first five; default-call latency."
    return report


def main():
    args = argparse.ArgumentParser(description=__doc__)
    mode = args.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate", action="store_true")
    mode.add_argument("--blank-review", type=Path, metavar="FILE")
    mode.add_argument("--run", type=Path, metavar="REPORT")
    args.add_argument("--repo", type=Path, default=HERE.parents[1])
    args.add_argument("--corpus", type=Path, default=HERE / "corpus.json")
    args.add_argument("--gold", type=Path, default=HERE / "provisional.json")
    args.add_argument("--follow-suggestions", action="store_true", help="Also measure the optional second search.")
    opts = args.parse_args()
    corpus = read(opts.corpus)
    validate_corpus(corpus)
    corpus_hash = fingerprint(opts.corpus)
    if opts.blank_review:
        write(opts.blank_review, review_form(corpus, corpus_hash), exclusive=True)
        return
    gold = read(opts.gold)
    validate_labels(corpus, gold, corpus_hash)
    if opts.validate:
        print(f"Valid: {len(corpus['items'])} items, {len(gold['negative_queries'])} extra negative queries")
        return
    repo = opts.repo.resolve()
    sha = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    backend_status = subprocess.check_output(
        ["git", "-C", str(repo), "status", "--porcelain", "--", "apps/backend"], text=True,
    )
    report = measure(repo, corpus, gold, follow_suggestions=opts.follow_suggestions)
    report.update({"code_sha": sha, "backend_tree_clean": not bool(backend_status.strip()),
                   "corpus_sha256": corpus_hash, "gold_sha256": fingerprint(opts.gold),
                   "evaluator_sha256": fingerprint(Path(__file__)), "gold_origin": gold["origin"],
                   "scope": "disposable_postgresql_text_service_only", "independent_user_uat": "NOT_RUN"})
    write(opts.run, report)
    print(json.dumps(report["overall"], ensure_ascii=True, indent=2))
    if report["correction_probe"]["status"] == "FAIL":
        raise SystemExit("Curated topic did not survive reorganization")
    if report["remove_wrong_auto_topic_probe"]["status"] == "FAIL":
        raise SystemExit("Report written: removing an incorrect automatic topic did not persist")


if __name__ == "__main__":
    main()
