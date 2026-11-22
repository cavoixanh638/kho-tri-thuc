"""P08/J9: actual 10k Item + 1k Topic PostgreSQL scale/retry/restore gate.

Intended for the existing isolated browser CI Compose project only, with two
dedicated databases; never opens Google Drive or touches a deployed service.
Invoke through Django manage.py shell in modes source/restore (env guards).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
from pathlib import Path
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client

from catalog.explorer import children
from catalog.knowledge_tree import tree
from catalog.models import Item, ItemTopic, Source, Topic
from ingestion.models import CaptureEvent
from ingestion.services import CaptureSubmission, submit_capture
from jobs.models import Job
from search.services import SearchFilters, SearchService

SOURCE_DB = "kt_p08_scale"
RESTORED_DB = "kt_p08_scale_restored"
OWNER = "p08-j9-scale-fixture"
FOREIGN_OWNER = "p08-j9-foreign-fixture"
ROOT = Path("/tmp/p08-j9-scale")
ITEMS = 10000
NODES = 1000
PAGE_SIZE = 100


def require(ok, code):
    if not ok:
        raise AssertionError("P08_J9_" + code)


def guard(mode):
    require(os.environ.get("P08_J9_ISOLATED") == "YES", "ISOLATION_FLAG_REQUIRED")
    require(os.environ.get("P08_J9_MODE") == mode, "MODE_MISMATCH")
    require(connection.vendor == "postgresql", "POSTGRESQL_REQUIRED")
    require(connection.settings_dict["NAME"] ==
            (SOURCE_DB if mode == "source" else RESTORED_DB),
            "DATABASE_NOT_ISOLATED")
    ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)


def report_json(filename, value):
    ROOT.joinpath(filename).write_text(
        json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def fingerprint():
    """SHA256 over all fixture-controlled identity, associations and timestamps."""
    sections = (
        ("catalog_item", Item.objects.order_by("id").values_list(
            "id", "owner_id", "kind", "title", "note", "saved_at",
            "updated_at", "home_topic_id", "parent_item_id")),
        ("catalog_topic", Topic.objects.order_by("id").values_list(
            "id", "owner_id", "parent_id", "name", "node_kind", "archived")),
        ("catalog_itemtopic", ItemTopic.objects.order_by("id").values_list(
            "id", "item_id", "topic_id", "origin", "user_pinned")),
        ("ingestion_captureevent", CaptureEvent.objects.order_by("id").values_list(
            "id", "owner_id", "item_id", "source_channel", "raw_kind",
            "raw_text", "original_url", "server_received_at", "idempotency_key")),
        ("catalog_source", Source.objects.order_by("id").values_list(
            "id", "item_id", "original_url", "canonical_url", "identity_hash")),
        ("jobs_job", Job.objects.order_by("id").values_list(
            "id", "item_id", "kind", "idempotency_key", "state")),
    )
    digest = hashlib.sha256()
    for label, query in sections:
        digest.update((label + "\n").encode("ascii"))
        for row in query.iterator(chunk_size=1000):
            digest.update(json.dumps(
                [str(value) if value is not None else None for value in row],
                ensure_ascii=False, separators=(",", ":"),
            ).encode("utf-8") + b"\n")
    return digest.hexdigest()


def counts(owner):
    return {
        "items": Item.objects.filter(owner=owner).count(),
        "topics": Topic.objects.filter(owner=owner).count(),
        "memberships": ItemTopic.objects.filter(item__owner=owner).count(),
        "events": CaptureEvent.objects.filter(owner=owner).count(),
        "sources": Source.objects.filter(item__owner=owner).count(),
        "jobs": Job.objects.filter(item__owner=owner).count(),
        "foreign_items": Item.objects.exclude(owner=owner).count(),
    }


def nearest_rank95(numbers):
    require(bool(numbers), "NO_LATENCY_SAMPLES")
    return round(sorted(numbers)[math.ceil(0.95 * len(numbers)) - 1], 3)


def seed():
    guard("source")
    require(not Item.objects.exists() and not Topic.objects.exists()
            and not CaptureEvent.objects.exists(), "SOURCE_DATABASE_NOT_EMPTY")
    users = get_user_model()
    owner = users.objects.create_user(username=OWNER, password=None)
    foreign = users.objects.create_user(username=FOREIGN_OWNER, password=None)

    # Keep a real hierarchy: 10 parents, 990 distinct children, 1,000 Topic rows.
    roots = Topic.objects.bulk_create([
        Topic(owner=owner, name=f"P08 J9 kho {i:02d}",
              node_kind=Topic.Kind.LIBRARY, sort_order=i) for i in range(10)
    ])
    leaves = Topic.objects.bulk_create([
        Topic(owner=owner, name=f"P08 J9 nhánh {i:04d}",
              parent=roots[i % len(roots)], node_kind=Topic.Kind.FOLDER,
              sort_order=i) for i in range(NODES - len(roots))
    ], batch_size=500)
    require(len(roots) + len(leaves) == NODES, "INVALID_TREE_SEED")

    sampled = {}
    sample_indices = {0, 1, 9, 10, 99, 999, 2222, 5678, 9001, 9999}
    for first in range(0, ITEMS, 1000):
        rows = []
        for i in range(first, min(first + 1000, ITEMS)):
            token = f"KTJ9TERM{i:05d}"
            obj = Item(owner=owner, kind="text", title=f"{token} nghiên cứu tiếng Việt",
                       note=f"# P08 J9 nội dung {i:05d}\n\nKiểm thử phân trang và phục hồi.\n",
                       home_topic=leaves[i % len(leaves)])
            rows.append(obj)
        Item.objects.bulk_create(rows, batch_size=500)
        ItemTopic.objects.bulk_create([
            ItemTopic(item=obj, topic_id=obj.home_topic_id,
                      origin="user", user_pinned=True) for obj in rows
        ], batch_size=500)
        for i, item in enumerate(rows, start=first):
            if i in sample_indices:
                sampled[i] = str(item.pk)

    # Other account's fixture is deliberately outside the 10,000 visible rows.
    Item.objects.create(owner=foreign, kind="text",
                        title="KTJ9PRIVATEOTHEROWNER", note="Không được rò rỉ.")
    require(counts(owner)["items"] == ITEMS, "SEED_COUNT")

    # Real service writes and PostgreSQL uniqueness under identical HTTP retry
    # keys. A new intentional send must create a new Event but reuse the Item.
    target = Item.objects.get(pk=UUID(sampled[0]), owner=owner)
    request = CaptureSubmission(
        kind="link", url="https://example.org/p08-j9-retry-synthetic",
        source_channel="web", target_item_id=target.pk,
        idempotency_key="p08-j9-request-key-001",
    )
    first_event, first_created = submit_capture(owner, request)
    again, again_created = submit_capture(owner, request)
    require(first_created and not again_created
            and first_event.pk == again.pk
            and first_event.server_received_at == again.server_received_at,
            "RETRY_CREATED_DUPLICATE")
    next_request = CaptureSubmission(
        kind="link", url=request.url, source_channel="web",
        target_item_id=target.pk, idempotency_key="p08-j9-request-key-002",
    )
    new_event, next_created = submit_capture(owner, next_request)
    require(next_created and new_event.pk != first_event.pk,
            "NEW_SEND_EVENT_MISSING")
    require(CaptureEvent.objects.filter(owner=owner).count() == 2,
            "CAPTURE_COUNT_WRONG")
    require(Source.objects.filter(item=target).count() == 1,
            "DUPLICATE_SOURCE")
    require(Job.objects.filter(item=target).count() == 1,
            "DUPLICATE_WORKER_JOB")
    require(Item.objects.filter(owner=owner).count() == ITEMS, "RETRY_CREATED_ITEM")

    # Actually call the session-authenticated Django REST endpoint for each
    # of 100 pages; no mock QuerySet, no skips, no truncated unique-ID sample.
    client = Client(HTTP_HOST="127.0.0.1")
    client.force_login(owner)
    seen = set()
    latencies = []
    first_page_ids = None
    for page in range(ITEMS // PAGE_SIZE):
        offset = page * PAGE_SIZE
        started = time.perf_counter_ns()
        response = client.get("/api/v1/items", data={
            "limit": PAGE_SIZE, "offset": offset,
        })
        latencies.append((time.perf_counter_ns() - started) / 1000000)
        require(response.status_code == 200, "REST_PAGE_HTTP_ERROR")
        payload = response.json()
        returned = [str(row["item_id"]) for row in payload["results"]]
        require(len(returned) == PAGE_SIZE, "SHORT_REST_PAGE")
        require(len(set(returned)) == PAGE_SIZE and not seen.intersection(returned),
                "DUPLICATE_PAGED_UUID")
        require(payload.get("next_offset") ==
                (offset + PAGE_SIZE if page < ITEMS // PAGE_SIZE - 1 else None),
                "PAGINATION_CURSOR_WRONG")
        seen.update(returned)
        if page == 0:
            first_page_ids = returned
    require(len(seen) == ITEMS, "MISSING_PAGED_UUID")
    first_again = client.get("/api/v1/items", data={
        "limit": PAGE_SIZE, "offset": 0,
    })
    require(first_again.status_code == 200
            and [str(row["item_id"]) for row in first_again.json()["results"]]
            == first_page_ids, "FIRST_PAGE_NOT_STABLE")

    nodes = tree(owner.pk)
    require(len(nodes) == NODES, "TREE_1000_NODES_MISSING")
    require(all(row["depth"] in (0, 1) for row in nodes), "TREE_DEPTH_INVALID")
    require(sum(row["direct_count"] for row in nodes) == ITEMS,
            "TREE_DIRECT_COUNT_WRONG")
    a = children(owner.pk, folder_id=roots[0].pk, offset=0, limit=50)
    b = children(owner.pk, folder_id=roots[0].pk, offset=50, limit=50)
    require(len(a["folders"]) == 50 and len(b["folders"]) == 49,
            "EXPLORER_FOLDER_PAGINATION_WRONG")
    require(not {row["id"] for row in a["folders"]}.intersection(
        row["id"] for row in b["folders"]), "EXPLORER_DUPLICATE_FOLDER")
    leaf_page = children(owner.pk, folder_id=leaves[0].pk, offset=0, limit=20)
    require(len(leaf_page["notes"]) in (10, 11), "EXPLORER_LEAF_ITEMS_WRONG")

    service = SearchService()
    search_times = []
    for index, expected_id in sorted(sampled.items()):
        query = f"KTJ9TERM{index:05d}"
        start = time.perf_counter_ns()
        hits = service.search(SearchFilters(owner_id=owner.pk), query, limit=5)
        search_times.append((time.perf_counter_ns() - start) / 1000000)
        require(expected_id in {str(hit.item_id) for hit in hits.hits},
                "SEARCH_MISSING_KNOWN_EXACT_TOKEN")
        require(all(Item.objects.filter(pk=hit.item_id, owner=owner).exists()
                    for hit in hits.hits), "SEARCH_FOREIGN_OWNER_RESULT")
    private = service.search(SearchFilters(owner_id=owner.pk),
                             "KTJ9PRIVATEOTHEROWNER", limit=5)
    require(not private.hits, "SEARCH_OWNER_ISOLATION_FAIL")

    stats = counts(owner)
    require(stats == {
        "items": ITEMS, "topics": NODES, "memberships": ITEMS,
        "events": 2, "sources": 1, "jobs": 1, "foreign_items": 1,
    }, "FINAL_COUNTS_INVALID")
    report = {
        "task": "P08/J9", "stage": "source", "status": "PASS",
        "source_database": SOURCE_DB, "restore_database": RESTORED_DB,
        "synthetic_only": True, "external_calls": 0, "counts": stats,
        "tree_nodes_verified": NODES, "rest_pages_verified": ITEMS // PAGE_SIZE,
        "rest_page_size": PAGE_SIZE, "rest_unique_item_ids": len(seen),
        "first_page_stable": True, "explorer_mixed_pagination": True,
        "search_queries_verified": len(sampled), "search_owner_isolated": True,
        "retry_same_key_same_event": True, "retry_new_send_adds_one_event": True,
        "retry_no_duplicate_source_job": True,
        "page_http_p95_ms": nearest_rank95(latencies),
        "search_service_p95_ms": nearest_rank95(search_times),
        "fingerprint_sha256": fingerprint(),
        "latency_scope": "isolated warm Django in-process Client and SQL; not production HTTP",
        "limitations": [
            "10,000 synthetic text Items, not 10,000 downloaded videos or 100GB Drive",
            "Search expected-token coverage, not relevance/semantic gold",
            "Full PostgreSQL database dump+restore/sha256 gate runs outside this script",
        ],
    }
    report_json("source.json", report)
    print(json.dumps({key: report[key] for key in (
        "task", "stage", "status", "counts", "rest_pages_verified",
        "rest_unique_item_ids", "search_queries_verified",
        "fingerprint_sha256",
    )}, ensure_ascii=False))


def restored():
    guard("restored")
    require(bool(re.fullmatch(r"[a-f0-9]{64}", os.environ.get(
        "P08_J9_BACKUP_SHA256", ""))), "BACKUP_SHA_MISSING")
    require(os.environ.get("P08_J9_BACKUP_VERIFIED") == "YES",
            "BACKUP_CHECKSUM_NOT_VERIFIED")
    source = json.loads(ROOT.joinpath("source.json").read_text(encoding="utf-8"))
    require(source["source_database"] == SOURCE_DB and
            source["status"] == "PASS", "SOURCE_EVIDENCE_INVALID")
    owner = get_user_model().objects.get(username=OWNER)
    stats = counts(owner)
    require(stats == source["counts"], "POST_RESTORE_COUNTS_DIFFER")
    digest = fingerprint()
    require(digest == source["fingerprint_sha256"], "POST_RESTORE_SHA256_DIFFER")
    require(Item.objects.filter(owner=owner).count() == ITEMS, "POST_RESTORE_ITEM_MISSING")
    require(Topic.objects.filter(owner=owner).count() == NODES, "POST_RESTORE_NODES_MISSING")
    require(not Item.objects.filter(title="KTJ9PRIVATEOTHEROWNER", owner=owner).exists(),
            "POST_RESTORE_OWNER_LEAK")

    # Same key after restore must remain idempotent; capture history isn't
    # reconstructed as a new Item or event by replay.
    original = CaptureEvent.objects.get(owner=owner,
        idempotency_key="p08-j9-request-key-001")
    retry = CaptureSubmission(
        kind="link", url="https://example.org/p08-j9-retry-synthetic",
        source_channel="web", target_item_id=original.item_id,
        idempotency_key="p08-j9-request-key-001",
    )
    duplicate, created = submit_capture(owner, retry)
    require(not created and duplicate.pk == original.pk,
            "POST_RESTORE_RETRY_CREATED_DUPLICATE")
    require(counts(owner) == stats and fingerprint() == digest,
            "REPLAY_ALTERED_RESTORED_DATABASE")

    report = {
        "task": "P08/J9", "stage": "restored", "status": "PASS",
        "source_database": SOURCE_DB, "restore_database": RESTORED_DB,
        "counts": stats, "fingerprint_sha256": digest,
        "post_restore_digest_equal": True,
        "post_restore_same_key_no_new_event": True,
        "backup_sha256": os.environ["P08_J9_BACKUP_SHA256"],
        "backup_checksum_verified": True, "postgres_custom_restore": True,
        "synthetic_only": True, "external_calls": 0,
        "media_drive_verified": False,
    }
    report_json("restored.json", report)
    print(json.dumps({key: report[key] for key in (
        "task", "stage", "status", "counts",
        "post_restore_digest_equal", "backup_sha256",
    )}, ensure_ascii=False))


# Executed directly by the isolated Django shell loader, never imported by
# production code. Every mode is guarded against non-QA database names.
mode = os.environ.get("P08_J9_MODE")
require(mode in ("source", "restored"), "INVALID_MODE")
(seed if mode == "source" else restored)()
