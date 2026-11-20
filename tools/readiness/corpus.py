"""Deterministic synthetic catalogue; import only after Django setup in the QA DB."""

import hashlib
import statistics
import time
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import NAMESPACE_URL, uuid5

from catalog.api import list_items
from catalog.knowledge_tree import tree
from catalog.models import Item, ItemTopic, RelatedItem, Source, Topic
from catalog.organization import OrganizationService
from django.contrib.auth import get_user_model
from django.db import transaction
from ingestion.models import CaptureEvent
from ingestion.services import CaptureSubmission, submit_capture
from processing.models import DerivedContent
from search.services import SearchFilters, SearchService
from storage.models import Asset, StorageLocation

PAYLOAD = b"KT114 synthetic original: Ti\xe1\xba\xbfng Vi\xe1\xbb\x87t\r\n"


def uid(key):
    return uuid5(NAMESPACE_URL, "https://kt114.example.invalid/" + key)


@transaction.atomic
def seed(count):
    if Item.objects.exists() or get_user_model().objects.exists():
        raise ValueError("Seed requires a fresh isolated database")
    owner = get_user_model().objects.create_user(username="kt114-fixture")
    roots, leaves = [], []
    paths = {}
    for r in range(2):
        root = Topic.objects.create(
            owner=owner, name=f"Kho thử {r}", node_kind="library"
        )
        roots.append(root)
        paths[root.pk] = [root.pk]
        for f in range(4):
            field = Topic.objects.create(
                owner=owner,
                parent=root,
                name=f"Lĩnh vực {r}-{f}",
                node_kind="field",
                sort_order=f,
            )
            paths[field.pk] = [root.pk, field.pk]
            for b in range(8):
                book = Topic.objects.create(
                    owner=owner,
                    parent=field,
                    name=f"Bộ sách {r}-{f}-{b}",
                    node_kind="book",
                    sort_order=b,
                )
                paths[book.pk] = [root.pk, field.pk, book.pk]
                chapter = Topic.objects.create(
                    owner=owner,
                    parent=book,
                    name="Chương tiếng Việt",
                    node_kind="chapter",
                )
                paths[chapter.pk] = [root.pk, field.pk, book.pk, chapter.pk]
                leaves.append(chapter)
    start = datetime(2026, 1, 1, tzinfo=UTC)
    items, events, assignments, assets, locations, sources, derived = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    expected = {pk: set() for pk in paths}
    sha = hashlib.sha256(PAYLOAD).hexdigest()
    for i in range(count):
        item_id = uid(f"item/{i}")
        note = f"# Tri thức tổng hợp {i}\r\nĐ/đ — tiếng Việt e\u0302\u0301; batbien{i:08d}\r\n\n| Cột | Dữ liệu |\n| --- | --- |\n| Số | {i} |\n"
        items.append(
            Item(
                id=item_id,
                owner=owner,
                kind="text",
                title=f"Bài fixture {i:05d}",
                note=note,
                saved_at=start + timedelta(seconds=i),
                favorite=i % 7 == 0,
                source_fetch="done",
                content_extract="done",
                asset_storage="not_applicable",
            )
        )
        events.append(
            CaptureEvent(
                id=uid(f"capture/{i}"),
                owner=owner,
                item_id=item_id,
                raw_kind="text",
                raw_text=note,
                source_channel="windows",
                server_received_at=start + timedelta(seconds=i),
                idempotency_key=f"kt114:{i}",
            )
        )
        selected = [leaves[i % len(leaves)]]
        if i % 10 == 0:
            selected.append(leaves[(i + 17) % len(leaves)])
        for leaf in selected:
            assignments.append(
                ItemTopic(
                    item_id=item_id,
                    topic=leaf,
                    origin="user",
                    user_pinned=True,
                    method_version="kt114-fixture-v1",
                    source_version=sha,
                )
            )
            for ancestor in paths[leaf.pk]:
                expected[ancestor].add(str(item_id))
        asset_id = uid(f"asset/{i}") if i % 100 == 0 else None
        if asset_id:
            assets.append(
                Asset(
                    id=asset_id,
                    item_id=item_id,
                    role="original",
                    mime="text/plain",
                    size=len(PAYLOAD),
                    sha256=sha,
                    original_filename=f"synthetic-{i}.txt",
                )
            )
            locations.append(
                StorageLocation(
                    asset_id=asset_id,
                    provider="google_drive",
                    provider_file_id=f"SYNTHETIC_NOT_A_DRIVE_FILE_{i}",
                    status="pending",
                    provider_revision="fixture-v1",
                )
            )
        if i % 2 == 0:
            url = f"https://example.invalid/kt114/{i}"
            sources.append(
                Source(
                    item_id=item_id,
                    original_url=url,
                    canonical_url=url,
                    identity_hash=hashlib.sha256(url.encode()).hexdigest(),
                    metadata={"fixture": True, "source_version": 1},
                )
            )
            derived.append(
                DerivedContent(
                    item_id=item_id,
                    asset_id=asset_id,
                    kind="web_text",
                    text=f"Văn bản trích tổng hợp {i}; truyvansau{i:08d}",
                    source_locator={
                        "page": i % 9 + 1,
                        "section": "Nguồn tổng hợp",
                        "schema_version": 1,
                    },
                    processor="kt114-fixture",
                    processor_version="v1",
                    input_hash=sha,
                )
            )
            if i % 20 == 0:
                derived.append(
                    DerivedContent(
                        item_id=item_id,
                        asset_id=asset_id,
                        kind="web_text",
                        text="Phiên bản cũ không dùng tìm kiếm",
                        source_locator={"page": 1},
                        processor="kt114-fixture",
                        processor_version="v0",
                        input_hash="0" * 64,
                        status="stale",
                    )
                )
    Item.objects.bulk_create(items, batch_size=500)
    CaptureEvent.objects.bulk_create(events, batch_size=500)
    ItemTopic.objects.bulk_create(assignments, batch_size=500)
    Asset.objects.bulk_create(assets, batch_size=500)
    StorageLocation.objects.bulk_create(locations, batch_size=500)
    Source.objects.bulk_create(sources, batch_size=500)
    DerivedContent.objects.bulk_create(derived, batch_size=500)
    relations = []
    for i in range(100):
        a, b = sorted([items[i].pk, items[i + 100].pk])
        relations.append(
            RelatedItem(
                item_a_id=a,
                item_b_id=b,
                reason="Fixture chỉ kiểm provenance, không đánh giá ngữ nghĩa",
                method_version="kt114-related-v1",
                source_version=sha,
            )
        )
    RelatedItem.objects.bulk_create(relations)
    return {
        "owner": owner,
        "roots": roots,
        "expected": expected,
        "ids": {str(i.pk) for i in items},
        "favorite_ids": {str(i.pk) for i in items if i.favorite},
    }


def paged(owner, **scope):
    ids, durations, offset = [], [], 0
    while True:
        begin = time.perf_counter()
        data = list_items(
            SimpleNamespace(user=owner), limit=100, offset=offset, **scope
        )
        durations.append((time.perf_counter() - begin) * 1000)
        ids.extend(str(row["item_id"]) for row in data["results"])
        if data["next_offset"] is None:
            break
        if data["next_offset"] <= offset:
            raise ValueError("Pagination did not progress")
        offset = data["next_offset"]
    return ids, durations


def evaluate(seed, count):
    owner = seed["owner"]
    begin = time.perf_counter()
    nodes = tree(owner.pk)
    tree_ms = (time.perf_counter() - begin) * 1000
    if any(n["item_count"] != len(seed["expected"][n["id"]]) for n in nodes):
        raise ValueError("Branch counts mismatch independent seed formula")
    pages, latencies = [], []
    scopes = [
        ("all", {}, seed["ids"]),
        ("favorite", {"favorite": True}, seed["favorite_ids"]),
    ]
    scopes += [
        (f"root_{i}", {"node_id": r.pk}, seed["expected"][r.pk])
        for i, r in enumerate(seed["roots"])
    ]
    for name, scope, expected in scopes:
        ids, times = paged(owner, **scope)
        if len(ids) != len(set(ids)) or set(ids) != expected:
            raise ValueError("Paged visible IDs differ from expected unique IDs")
        pages.append(
            {
                "scope": name,
                "expected_unique": len(expected),
                "displayed_unique": len(set(ids)),
                "difference": len(set(ids)) - len(expected),
                "pages": len(times),
                "duplicate_rows": len(ids) - len(set(ids)),
            }
        )
        latencies.extend(times)
    if Item.objects.count() != count:
        raise ValueError("Read-only views changed item count")
    pinned_before = list(
        ItemTopic.objects.filter(item_id=uid("item/0")).order_by("id").values()
    )
    OrganizationService().organize(uid("item/0"))
    pinned_after = list(
        ItemTopic.objects.filter(item_id=uid("item/0"), user_pinned=True)
        .order_by("id")
        .values()
    )
    if pinned_before != pinned_after:
        raise ValueError("Organization changed pinned assignments")
    before = CaptureEvent.objects.count()
    submission = CaptureSubmission(
        kind="link",
        url="https://example.com/kt114-fixture",
        text="Chú thích Việt nguyên văn\r\n",
        source_channel="windows",
        idempotency_key="kt114:new-send-1",
    )
    event, _ = submit_capture(owner, submission)
    replay, created = submit_capture(owner, submission)
    if replay.pk != event.pk or created or CaptureEvent.objects.count() != before + 1:
        raise ValueError("Retry duplicated the capture")
    second, _ = submit_capture(
        owner,
        CaptureSubmission(
            kind="link",
            url=submission.url,
            text="Lượt gửi mới có chú thích khác",
            source_channel="windows",
            idempotency_key="kt114:new-send-2",
        ),
    )
    if (
        second.pk == event.pk
        or second.item_id != event.item_id
        or CaptureEvent.objects.count() != before + 2
    ):
        raise ValueError("New send did not preserve source identity and new history")
    search = SearchService()
    item_hit = uid("item/9999") in {
        r.item_id
        for r in search.search(SearchFilters(owner_id=owner.pk), "batbien00009999").hits
    }
    derived_hit = uid("item/9998") in {
        r.item_id
        for r in search.search(
            SearchFilters(owner_id=owner.pk), "truyvansau00009998"
        ).hits
    }
    if not item_hit or not derived_hit:
        raise ValueError("Search failed to find item/derived evidence")
    return {
        "initial_unique_items": count,
        "tree_nodes": len(nodes),
        "tree_ms": round(tree_ms, 2),
        "all_node_counts_match": True,
        "pagination": pages,
        "page_latency_ms": {
            "median": round(statistics.median(latencies), 2),
            "p95": round(sorted(latencies)[int((len(latencies) - 1) * 0.95)], 2),
            "max": round(max(latencies), 2),
            "scope": "local synthetic corpus, view service calls, no network/browser",
        },
        "pinned_relations_unchanged": True,
        "new_sends_event_delta": 2,
        "same_key_retry_delta": 0,
        "same_source_item_preserved": True,
        "post_capture_item_count": Item.objects.count(),
        "item_and_derived_search_hits": True,
    }
