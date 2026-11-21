"""P09: independent black-box KT122/123 hierarchy audit on frozen code.

Run: python manage.py test catalog.test_parallel_explorer -v 2
Optional scale: P09_SCALE=1 python manage.py test catalog.test_parallel_explorer -v 2
No production database, Drive files, or CaptureEvent are modified.
"""

import json
import os
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from statistics import quantiles
from threading import Barrier
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection
from django.test import Client, TransactionTestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from ingestion.models import CaptureEvent
from jobs.models import Job
from storage.models import Asset

from . import explorer
from .knowledge_tree import save_node, tree
from .models import Item, ItemTopic, Topic

RAW = "  Ghi chú Tiếng Việt\r\n# Không chuẩn hóa\n"


class P09HierarchyAudit(TransactionTestCase):
    """Only public /api/v1 routes mutate data; fixtures use isolated test DB."""

    def setUp(self):
        users = get_user_model()
        self.owner = users.objects.create_user(username="p09-owner")
        self.other = users.objects.create_user(username="p09-other")
        self.client.force_login(self.owner)
        self.folder = Topic.objects.create(owner=self.owner, name="Sách")
        self.foreign_folder = Topic.objects.create(owner=self.other, name="Private")
        self.archived_folder = Topic.objects.create(owner=self.owner, name="Archived", archived=True)
        self.item = Item.objects.create(
            owner=self.owner, kind="text", title="Original", note=RAW,
            home_topic=self.folder,
        )
        ItemTopic.objects.create(item=self.item, topic=self.folder, user_pinned=True)
        self.foreign_item = Item.objects.create(owner=self.other, kind="text", note="private")
        self.deleted_item = Item.objects.create(
            owner=self.owner, kind="text", deleted_at=timezone.now()
        )

    def api(self, method, path, body=None, *, client=None, headers=None):
        client = client or self.client
        url = "/api/v1" + path
        if method == "GET":
            return client.get(url)
        return getattr(client, method.lower())(
            url, body if body is not None else {},
            content_type="application/json", headers=headers or {},
        )

    def placement(self, action, folder_id, expected_version=0, item=None):
        item = item or self.item
        return self.api(
            "PATCH", f"/items/{item.pk}/placement",
            {"action": action, "folder_id": folder_id, "expected_version": expected_version},
        )

    def structure(self, item, parent_id, version=0, order=0):
        return self.api(
            "PATCH", f"/items/{item.pk}/structure",
            {"parent_item_id": str(parent_id) if parent_id is not None else None,
             "sort_order": order, "expected_version": version},
        )

    def snapshot(self):
        self.item.refresh_from_db()
        return (
            Item.objects.count(), ItemTopic.objects.count(),
            CaptureEvent.objects.count(), Job.objects.count(),
            self.item.note, self.item.home_topic_id,
            self.item.parent_item_id, self.item.structure_version,
        )

    def test_43_bad_api_cases_fail_without_mutating_any_items_events_or_jobs(self):
        ppath = f"/items/{self.item.pk}/placement"
        spath = f"/items/{self.item.pk}/structure"
        p = lambda **kw: dict(action="move", folder_id=self.folder.pk, expected_version=0, **kw)
        s = lambda **kw: dict(parent_item_id=None, sort_order=0, expected_version=0, **kw)
        n = lambda **kw: dict(text="fixture", title="Safe", **kw)
        # Replace fields explicitly instead of passing duplicate kwargs.
        p0 = {"action": "move", "folder_id": self.folder.pk, "expected_version": 0}
        s0 = {"parent_item_id": None, "sort_order": 0, "expected_version": 0}
        def change(base, **kwargs):
            return {**base, **kwargs}
        cases = [
            ("PATCH", ppath, change(p0, action="rename"), 422),
            ("PATCH", ppath, change(p0, action="add", folder_id=None), 422),
            ("PATCH", ppath, change(p0, action="remove", folder_id=None), 422),
            ("PATCH", ppath, change(p0, folder_id=0), 422),
            ("PATCH", ppath, change(p0, folder_id=-1), 422),
            ("PATCH", ppath, change(p0, folder_id="NaN"), 422),
            ("PATCH", ppath, change(p0, folder_id=self.foreign_folder.pk), 404),
            ("PATCH", ppath, change(p0, folder_id=self.archived_folder.pk), 404),
            ("PATCH", ppath, change(p0, folder_id=2_000_000_001), 404),
            ("PATCH", ppath, change(p0, expected_version=-1), 422),
            ("PATCH", ppath, change(p0, expected_version=True), 422),
            ("PATCH", ppath, change(p0, expected_version="0"), 422),
            ("PATCH", ppath, change(p0, expected_version=1), 409),
            ("PATCH", ppath, {"action": "move", "folder_id": None}, 422),
            ("PATCH", spath, change(s0, parent_item_id=str(self.item.pk)), 422),
            ("PATCH", spath, change(s0, parent_item_id=str(self.foreign_item.pk)), 404),
            ("PATCH", spath, change(s0, parent_item_id=str(self.deleted_item.pk)), 404),
            ("PATCH", spath, change(s0, parent_item_id=str(uuid4())), 404),
            ("PATCH", spath, change(s0, parent_item_id="bad-uuid"), 422),
            ("PATCH", spath, change(s0, expected_version=-1), 422),
            ("PATCH", spath, change(s0, expected_version=True), 422),
            ("PATCH", spath, change(s0, expected_version="0"), 422),
            ("PATCH", spath, change(s0, expected_version=1), 409),
            ("PATCH", spath, change(s0, sort_order=-1), 422),
            ("PATCH", spath, change(s0, sort_order=1_000_001), 422),
            ("PATCH", spath, change(s0, sort_order="word"), 422),
            ("PATCH", spath, {"parent_item_id": None}, 422),
            ("GET", "/explorer/children?limit=0", None, 422),
            ("GET", "/explorer/children?limit=101", None, 422),
            ("GET", "/explorer/children?offset=-1", None, 422),
            ("GET", "/explorer/children?folder_id=0", None, 422),
            ("GET", "/explorer/children?folder_id=wat", None, 422),
            ("GET", f"/explorer/children?folder_id={self.foreign_folder.pk}", None, 404),
            ("GET", "/explorer/children?parent_item_id=garbage", None, 422),
            ("GET", f"/explorer/children?parent_item_id={self.foreign_item.pk}", None, 404),
            ("GET", "/explorer/children?unfiled=perhaps", None, 422),
            ("POST", "/explorer/notes", change(n(), text=""), 422),
            ("POST", "/explorer/notes", change(n(), text="x" * 65537), 422),
            ("POST", "/explorer/notes", change(n(), title="x" * 513), 422),
            ("POST", "/explorer/notes", change(n(), title="NUL\x00"), 422),
            ("POST", "/explorer/notes", change(n(), home_topic_id=self.foreign_folder.pk), 404),
            ("POST", "/explorer/notes", change(n(), home_topic_id=self.archived_folder.pk), 404),
            ("POST", "/explorer/notes", change(n(), parent_item_id=str(self.foreign_item.pk)), 404),
            ("POST", "/explorer/notes", change(n(), parent_item_id=str(self.deleted_item.pk)), 404),
        ]
        self.assertGreaterEqual(len(cases), 30)
        original = self.snapshot()
        for index, (method, path, payload, status) in enumerate(cases, 1):
            with self.subTest(index=index, method=method, path=path):
                response = self.api(method, path, payload)
                self.assertEqual(response.status_code, status, response.content[:300])
                self.assertEqual(self.snapshot(), original)

    def test_five_levels_three_folders_one_uuid_and_parent_without_new_capture(self):
        nodes, parent = [], None
        for depth in range(5):
            folder, created = save_node(
                self.owner.pk, name=f"Level-{depth}", parent_id=parent,
                node_kind="folder",
            )
            self.assertTrue(created)
            nodes.append(folder)
            parent = folder.pk
        payload = {"text": RAW, "title": "Ghi chú duy nhất", "home_topic_id": nodes[-1].pk}
        headers = {"Idempotency-Key": "p09-same-attempt"}
        first = self.api("POST", "/explorer/notes", payload, headers=headers)
        replay = self.api("POST", "/explorer/notes", payload, headers=headers)
        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(replay.status_code, 200, replay.content)
        self.assertEqual(first.json(), replay.json())
        item_id = first.json()["item_id"]
        event = CaptureEvent.objects.get(pk=first.json()["capture_id"])
        captured_at = event.server_received_at
        for version, folder in enumerate((nodes[0], nodes[2])):
            placed = self.api(
                "PATCH", f"/items/{item_id}/placement",
                {"action": "add", "folder_id": folder.pk, "expected_version": version},
            )
            self.assertEqual(placed.status_code, 200, placed.content)
        relation = self.api(
            "PATCH", f"/items/{item_id}/structure",
            {"parent_item_id": str(self.item.pk), "sort_order": 7, "expected_version": 2},
        )
        self.assertEqual(relation.status_code, 200, relation.content)
        entry = Item.objects.get(pk=item_id)
        self.assertEqual(entry.note.encode(), RAW.encode())
        self.assertEqual(entry.parent_item_id, self.item.pk)
        self.assertEqual(entry.home_topic_id, nodes[4].pk)
        self.assertEqual(Item.objects.filter(pk=item_id).count(), 1)
        self.assertEqual(ItemTopic.objects.filter(item_id=item_id).count(), 3)
        self.assertEqual(CaptureEvent.objects.filter(item_id=item_id).count(), 1)
        self.assertEqual(Job.objects.filter(item_id=item_id).count(), 1)
        for folder in (nodes[0], nodes[2], nodes[4]):
            data = self.api("GET", f"/explorer/children?folder_id={folder.pk}").json()
            found = next(row for row in data["notes"] if row["item_id"] == item_id)
            self.assertTrue(found["shortcut"])
        child = self.api("GET", f"/explorer/children?parent_item_id={self.item.pk}").json()
        self.assertIn(item_id, [row["item_id"] for row in child["notes"]])
        self.assertEqual(next(n for n in tree(self.owner.pk) if n["id"] == nodes[0].pk)["item_count"], 1)
        event.refresh_from_db()
        self.assertEqual(event.server_received_at, captured_at)
        self.assertEqual(event.raw_text, RAW)

    def test_owner_isolation_for_read_write_archive_and_find(self):
        self.client.force_login(self.other)
        for path in (
            f"/items/{self.item.pk}/placement",
            f"/items/{self.item.pk}/structure",
            f"/explorer/children?folder_id={self.folder.pk}",
        ):
            self.assertEqual(self.api("GET", path).status_code, 404)
        self.assertEqual(self.placement("move", self.foreign_folder.pk).status_code, 404)
        self.assertEqual(self.structure(self.item, self.foreign_item.pk).status_code, 404)
        self.assertEqual(self.api("DELETE", f"/explorer/folders/{self.folder.pk}").status_code, 404)
        self.assertNotIn(str(self.item.pk), self.api("GET", "/explorer/find?q=Original").content.decode())
        self.client.logout()
        self.assertEqual(self.api("GET", "/explorer/children").status_code, 401)
        self.assertEqual(self.api("POST", "/explorer/notes", {"text": "x"}).status_code, 401)

    def test_moving_renaming_and_reordering_preserve_raw_receipt_asset_and_job(self):
        event = CaptureEvent.objects.create(
            owner=self.owner, item=self.item, raw_kind="text", raw_text=RAW
        )
        asset = Asset.objects.create(
            item=self.item, mime="application/pdf", sha256="d" * 64, size=512,
            original_filename="synthetic-test.pdf",
        )
        original = (self.item.note, event.pk, event.server_received_at, asset.pk,
                    CaptureEvent.objects.count(), Job.objects.count())
        self.assertEqual(self.placement("move", None).status_code, 200)
        self.assertEqual(self.structure(self.item, None, version=1, order=11).status_code, 200)
        rename = self.api("PATCH", f"/items/{self.item.pk}",
                          {"title": "Renamed", "expected_edit_version": 0})
        self.assertEqual(rename.status_code, 200, rename.content)
        self.item.refresh_from_db()
        event.refresh_from_db()
        asset.refresh_from_db()
        self.assertEqual(
            (self.item.note, event.pk, event.server_received_at, asset.pk,
             CaptureEvent.objects.count(), Job.objects.count()), original
        )
        self.assertEqual(self.item.title, "Renamed")

    def test_unfiled_explorer_and_library_agree_on_active_shortcuts(self):
        """A live shortcut is a visible placement even after the home is unset."""
        self.assertEqual(self.placement("move", None).status_code, 200)
        self.assertTrue(ItemTopic.objects.filter(item=self.item, topic=self.folder).exists())
        explorer_page = self.api("GET", "/explorer/children?unfiled=true")
        library_page = self.api("GET", "/items?unfiled=true")
        self.assertEqual(explorer_page.status_code, 200)
        self.assertEqual(library_page.status_code, 200)
        ids = {row["item_id"] for row in explorer_page.json()["notes"]}
        listed = {row["id"] for row in library_page.json()["results"]}
        self.assertNotIn(str(self.item.pk), ids)
        self.assertNotIn(str(self.item.pk), listed)
        # Removing the last visible placement makes the note genuinely unfiled.
        ItemTopic.objects.filter(item=self.item).delete()
        explorer_page = self.api("GET", "/explorer/children?unfiled=true")
        library_page = self.api("GET", "/items?unfiled=true")
        self.assertIn(str(self.item.pk), {row["item_id"] for row in explorer_page.json()["notes"]})
        self.assertIn(str(self.item.pk), {row["id"] for row in library_page.json()["results"]})

    def test_stable_root_pagination_125_items_115_folders_no_private_body(self):
        notes = Item.objects.bulk_create([
            Item(owner=self.owner, kind="text", title=f"root-{i:04d}",
                 note="PRIVATE BODY" * 1000) for i in range(125)
        ])
        folders = Topic.objects.bulk_create([
            Topic(owner=self.owner, name=f"root-folder-{i:04d}") for i in range(115)
        ])
        seen_notes, seen_folders, offset = [], [], 0
        while offset is not None:
            result = self.api("GET", f"/explorer/children?offset={offset}&limit=25")
            self.assertEqual(result.status_code, 200, result.content)
            data = result.json()
            self.assertLessEqual(len(data["notes"]), 25)
            self.assertLessEqual(len(data["folders"]), 25)
            self.assertTrue(all("note" not in row for row in data["notes"]))
            seen_notes.extend(row["item_id"] for row in data["notes"])
            seen_folders.extend(row["id"] for row in data["folders"])
            offset = data["next_offset"]
        self.assertEqual(set(seen_notes), {str(item.pk) for item in notes})
        self.assertEqual(len(seen_notes), 125)
        self.assertEqual(set(seen_folders), {self.folder.pk, *[f.pk for f in folders]})
        self.assertEqual(len(seen_folders), 116)

    def test_simultaneous_reverse_edges_never_commit_cycle(self):
        peer = Item.objects.create(owner=self.owner, kind="text")
        barrier = Barrier(2)
        def move(source, parent):
            close_old_connections()
            try:
                client = Client()
                client.force_login(self.owner)
                barrier.wait(timeout=15)
                response = client.patch(
                    f"/api/v1/items/{source}/structure",
                    {"parent_item_id": str(parent), "expected_version": 0},
                    content_type="application/json",
                )
                return response.status_code
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda edge: move(*edge), [
                (self.item.pk, peer.pk), (peer.pk, self.item.pk)
            ]))
        self.assertEqual(sorted(results), [200, 422])
        self.item.refresh_from_db()
        peer.refresh_from_db()
        self.assertFalse(self.item.parent_item_id == peer.pk and peer.parent_item_id == self.item.pk)

    def test_soft_deleted_parent_keeps_child_and_capture_receipt(self):
        child = Item.objects.create(owner=self.owner, kind="text", note=RAW, parent_item=self.item)
        event = CaptureEvent.objects.create(owner=self.owner, item=child, raw_kind="text", raw_text=RAW)
        original = event.server_received_at
        self.item.deleted_at = timezone.now()
        self.item.save(update_fields=["deleted_at"])
        response = self.api("GET", "/explorer/children?unfiled=true")
        self.assertEqual(response.status_code, 200)
        self.assertIn(str(child.pk), [n["item_id"] for n in response.json()["notes"]])
        self.assertEqual(Item.objects.get(pk=child.pk).note, RAW)
        event.refresh_from_db()
        self.assertEqual(event.server_received_at, original)

    def test_depth_64_is_allowed_65th_rejected_without_mutation(self):
        current = self.item
        for i in range(explorer.MAX_DEPTH - 1):
            child = Item.objects.create(owner=self.owner, kind="text", note=f"level-{i}")
            result = self.structure(child, current.pk)
            self.assertEqual(result.status_code, 200, result.content)
            current = child
        overflow = Item.objects.create(owner=self.owner, kind="text", note=RAW)
        result = self.structure(overflow, current.pk)
        self.assertEqual(result.status_code, 422, result.content)
        overflow.refresh_from_db()
        self.assertIsNone(overflow.parent_item_id)
        self.assertEqual(overflow.note, RAW)

    def test_five_level_archive_never_deletes_note_or_receipt(self):
        chain, parent = [], None
        for i in range(5):
            folder, _ = save_node(
                self.owner.pk, name=f"Archive-{i}", parent_id=parent,
                node_kind="folder",
            )
            chain.append(folder)
            parent = folder.pk
        self.assertEqual(self.placement("move", chain[-1].pk).status_code, 200)
        event = CaptureEvent.objects.create(owner=self.owner, item=self.item, raw_kind="text", raw_text=RAW)
        original = event.server_received_at
        result = self.api("DELETE", f"/explorer/folders/{chain[0].pk}")
        self.assertEqual(result.status_code, 200, result.content)
        self.assertEqual(Topic.objects.filter(pk__in=[n.pk for n in chain], archived=True).count(), 5)
        self.item.refresh_from_db()
        event.refresh_from_db()
        self.assertEqual(self.item.note, RAW)
        self.assertEqual(event.server_received_at, original)
        page = self.api("GET", "/explorer/children?unfiled=true").json()
        self.assertIn(str(self.item.pk), [r["item_id"] for r in page["notes"]])

    @unittest.skipUnless(os.getenv("P09_SCALE") == "1", "opt-in 10000 Item/1000 folder PostgreSQL audit")
    def test_opt_in_10000_items_1000_folders_p95_query_count(self):
        folders = Topic.objects.bulk_create([
            Topic(owner=self.owner, name=f"P09-scale-{i:04d}") for i in range(1000)
        ])
        notes = Item.objects.bulk_create([
            Item(owner=self.owner, kind="text", title=f"P09-note-{i:05d}",
                 note="synthetic" * 100, home_topic=folders[i % 1000])
            for i in range(10000)
        ])
        ItemTopic.objects.bulk_create([
            ItemTopic(item=item, topic=folders[i % 1000], user_pinned=True)
            for i, item in enumerate(notes)
        ])
        samples, queries = [], []
        for i in range(30):
            with CaptureQueriesContext(connection) as measured:
                started = time.perf_counter()
                page = explorer.children(self.owner.pk, folder_id=folders[i].pk)
                samples.append((time.perf_counter() - started) * 1000)
            queries.append(len(measured))
            self.assertEqual(len(page["notes"]), 10)
        p95 = quantiles(samples, n=100, method="inclusive")[94]
        print("P09_SCALE " + json.dumps({
            "items": 10000, "folders": 1000, "samples": 30,
            "p95_ms": round(p95, 3), "max_queries": max(queries),
        }, sort_keys=True))
        self.assertLessEqual(max(queries), 5)
