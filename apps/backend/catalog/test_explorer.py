"""KT122/123 real PostgreSQL API, ownership, cycle and bounded reads."""

import json
import os
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from statistics import quantiles
from threading import Barrier

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


class ExplorerTests(TransactionTestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="explorer-owner")
        self.other = get_user_model().objects.create_user(username="explorer-other")
        self.client.force_login(self.owner)
        self.folder = Topic.objects.create(owner=self.owner, name="Sách")
        self.item = Item.objects.create(
            owner=self.owner,
            kind="text",
            title="Bài gốc",
            note="Tiếng Việt\r\n",
            home_topic=self.folder,
        )
        ItemTopic.objects.create(
            item=self.item, topic=self.folder, origin="user", user_pinned=True
        )

    def patch(self, path, body):
        return self.client.patch(
            "/api/v1" + path, body, content_type="application/json"
        )

    def create(self, text="Nội dung", folder=None, parent=None, key="fixture-create"):
        return self.client.post(
            "/api/v1/explorer/notes",
            {
                "text": text,
                "title": "Ghi chú mới",
                "home_topic_id": folder,
                "parent_item_id": str(parent) if parent else None,
            },
            content_type="application/json",
            headers={"Idempotency-Key": key},
        )

    def test_ten_create_receipts_commit_home_and_retry_zero_new_event(self):
        for index in range(10):
            raw = f"  Ghi chú {index} Tiếng Việt\r\n"
            first = self.create(raw, self.folder.pk, key=f"create-{index}")
            self.assertEqual(first.status_code, 201, first.content)
            replay = self.create(raw, self.folder.pk, key=f"create-{index}")
            self.assertEqual(replay.status_code, 200)
            self.assertEqual(replay.json(), first.json())
            item = Item.objects.get(pk=first.json()["item_id"])
            self.assertEqual(item.note.encode(), raw.encode())
            self.assertEqual(item.home_topic_id, self.folder.pk)
            self.assertTrue(
                ItemTopic.objects.get(item=item, topic=self.folder).user_pinned
            )
        self.assertEqual(CaptureEvent.objects.count(), 10)
        self.assertEqual(Job.objects.count(), 10)

    def test_invalid_home_or_parent_rolls_back_capture_item_job_together(self):
        before = (
            Item.objects.count(),
            CaptureEvent.objects.count(),
            Job.objects.count(),
        )
        foreign = Topic.objects.create(owner=self.other, name="Không được")
        invalid = self.create(folder=foreign.pk)
        self.assertEqual(invalid.status_code, 404)
        self.assertEqual(
            (Item.objects.count(), CaptureEvent.objects.count(), Job.objects.count()),
            before,
        )
        deleted = Item.objects.create(
            owner=self.owner, kind="text", deleted_at=timezone.now()
        )
        before = (
            Item.objects.count(),
            CaptureEvent.objects.count(),
            Job.objects.count(),
        )
        invalid = self.create(parent=deleted.pk)
        self.assertEqual(invalid.status_code, 404)
        self.assertEqual(
            (Item.objects.count(), CaptureEvent.objects.count(), Job.objects.count()),
            before,
        )

    def test_one_note_three_folders_keeps_identity_history_assets_and_home_on_move(
        self,
    ):
        folders = [self.folder] + [
            Topic.objects.create(owner=self.owner, name=f"Nhánh {i}") for i in range(3)
        ]
        event = CaptureEvent.objects.create(
            owner=self.owner, item=self.item, raw_kind="text", raw_text=self.item.note
        )
        asset = Asset.objects.create(
            item=self.item,
            mime="application/pdf",
            sha256="a" * 64,
            size=12,
            original_filename="synthetic.pdf",
        )
        snapshot = (
            event.server_received_at,
            event.raw_text,
            asset.pk,
            self.item.note,
            Item.objects.count(),
            CaptureEvent.objects.count(),
            Job.objects.count(),
        )
        version = 0
        for folder in folders[1:3]:
            result = self.patch(
                f"/items/{self.item.pk}/placement",
                {"action": "add", "folder_id": folder.pk, "expected_version": version},
            )
            self.assertEqual(result.status_code, 200, result.content)
            version += 1
        moved = self.patch(
            f"/items/{self.item.pk}/placement",
            {"action": "move", "folder_id": folders[3].pk, "expected_version": version},
        )
        self.assertEqual(moved.status_code, 200, moved.content)
        self.item.refresh_from_db()
        event.refresh_from_db()
        self.assertEqual(self.item.home_topic_id, folders[3].pk)
        self.assertEqual(ItemTopic.objects.filter(item=self.item).count(), 4)
        for folder in folders:
            page = self.client.get(
                f"/api/v1/explorer/children?folder_id={folder.pk}"
            ).json()
            self.assertEqual(
                [row["item_id"] for row in page["notes"]], [str(self.item.pk)]
            )
            self.assertEqual(page["notes"][0]["shortcut"], folder.pk != folders[3].pk)
        self.assertEqual(
            (
                event.server_received_at,
                event.raw_text,
                asset.pk,
                self.item.note,
                Item.objects.count(),
                CaptureEvent.objects.count(),
                Job.objects.count(),
            ),
            snapshot,
        )

    def test_version_conflict_no_mutation_and_schema_validation(self):
        first = self.patch(
            f"/items/{self.item.pk}/placement",
            {"action": "move", "folder_id": None, "expected_version": 0},
        )
        self.assertEqual(first.status_code, 200)
        before = Item.objects.values().get(pk=self.item.pk)
        conflict = self.patch(
            f"/items/{self.item.pk}/placement",
            {"action": "move", "folder_id": self.folder.pk, "expected_version": 0},
        )
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(Item.objects.values().get(pk=self.item.pk), before)
        for version in (-1, True, "1", 0.2):
            with self.subTest(version=version):
                self.assertEqual(
                    self.patch(
                        f"/items/{self.item.pk}/structure",
                        {"parent_item_id": None, "expected_version": version},
                    ).status_code,
                    422,
                )

    def test_auth_owner_soft_deleted_and_archived_guards(self):
        self.client.logout()
        for path in (
            "/explorer/children",
            f"/items/{self.item.pk}/structure",
            f"/items/{self.item.pk}/placement",
        ):
            self.assertEqual(self.client.get("/api/v1" + path).status_code, 401)
        self.client.force_login(self.other)
        for path in (
            f"/items/{self.item.pk}/structure",
            f"/items/{self.item.pk}/placement",
            f"/explorer/children?folder_id={self.folder.pk}",
        ):
            self.assertEqual(self.client.get("/api/v1" + path).status_code, 404)
        self.client.force_login(self.owner)
        self.item.deleted_at = timezone.now()
        self.item.save()
        self.assertEqual(
            self.client.get(f"/api/v1/items/{self.item.pk}/structure").status_code, 404
        )
        self.assertEqual(
            self.client.get(
                f"/api/v1/explorer/children?folder_id={self.folder.pk}"
            ).json()["notes"],
            [],
        )
        self.folder.archived = True
        self.folder.save()
        self.assertEqual(self.create(folder=self.folder.pk).status_code, 404)

    def test_csrf_required_for_all_mutation_routes(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        for method, path, body in (
            ("post", "/explorer/notes", {"text": "x"}),
            (
                "patch",
                f"/items/{self.item.pk}/structure",
                {"parent_item_id": None, "expected_version": 0},
            ),
            (
                "patch",
                f"/items/{self.item.pk}/placement",
                {"action": "move", "folder_id": None, "expected_version": 0},
            ),
            ("delete", f"/explorer/folders/{self.folder.pk}", {}),
        ):
            with self.subTest(path=path):
                self.assertEqual(
                    getattr(client, method)(
                        "/api/v1" + path, body, content_type="application/json"
                    ).status_code,
                    403,
                )

    def test_folder_five_levels_duplicate_unicode_cycle_and_archive_keep_notes(self):
        parent = None
        nodes = []
        for index in range(5):
            node, _ = save_node(
                self.owner.pk,
                name=f"Tầng {index}",
                parent_id=parent,
                node_kind="folder",
            )
            nodes.append(node)
            parent = node.pk
        result = self.patch(
            f"/knowledge-tree/{nodes[0].pk}",
            {
                "name": nodes[0].name,
                "parent_id": nodes[-1].pk,
                "node_kind": "folder",
                "sort_order": 0,
            },
        )
        self.assertEqual(result.status_code, 422)
        original, _ = save_node(
            self.owner.pk, name="Tiếng", parent_id=None, node_kind="folder"
        )
        same, created = save_node(
            self.owner.pk, name="Tiếng", parent_id=None, node_kind="folder"
        )
        self.assertEqual(original.pk, same.pk)
        self.assertFalse(created)
        self.item.home_topic = nodes[-1]
        self.item.save()
        ItemTopic.objects.create(item=self.item, topic=nodes[-1], user_pinned=True)
        archived = self.client.delete(f"/api/v1/explorer/folders/{nodes[0].pk}")
        self.assertEqual(archived.status_code, 200)
        self.assertEqual(
            Topic.objects.filter(pk__in=[n.pk for n in nodes], archived=True).count(), 5
        )
        self.assertEqual(
            self.client.get("/api/v1/explorer/children?unfiled=true").json()["notes"][
                0
            ]["item_id"],
            str(self.item.pk),
        )

    def test_two_parents_twenty_children_three_levels_and_separate_related(self):
        parents = [
            self.item,
            Item.objects.create(owner=self.owner, kind="text", title="Sách thứ hai"),
        ]
        children = []
        for index in range(20):
            result = self.create(
                text=f"Chương {index}",
                folder=self.folder.pk,
                parent=parents[index % 2].pk,
                key=f"chapter-{index}",
            )
            self.assertEqual(result.status_code, 201, result.content)
            children.append(Item.objects.get(pk=result.json()["item_id"]))
        third = self.create(
            text="Mục con", parent=children[0].pk, key="grandchild"
        ).json()
        info = self.client.get(f"/api/v1/items/{third['item_id']}/structure").json()
        self.assertEqual(
            [row["item_id"] for row in info["ancestors"]],
            [str(self.item.pk), str(children[0].pk)],
        )
        self.assertEqual(info["origin"], "user")
        self.assertEqual(
            self.client.get(f"/api/v1/items/{self.item.pk}/structure")
            .json()["children"]
            .__len__(),
            10,
        )
        page = self.client.get(
            f"/api/v1/explorer/children?folder_id={self.folder.pk}"
        ).json()
        self.assertTrue(
            next(row for row in page["notes"] if row["item_id"] == str(children[0].pk))[
                "shortcut"
            ]
        )
        self.assertEqual(CaptureEvent.objects.count(), 21)

    def test_cycle_lengths_two_three_four_and_self_leave_no_bad_edge(self):
        for length in (1, 2, 3, 4):
            nodes = [
                Item.objects.create(owner=self.owner, kind="text")
                for _ in range(length)
            ]
            for index in range(length - 1):
                explorer.structure(
                    self.owner.pk,
                    nodes[index + 1].pk,
                    parent_item_id=nodes[index].pk,
                    sort_order=index,
                    expected_version=0,
                )
            response = self.patch(
                f"/items/{nodes[0].pk}/structure",
                {"parent_item_id": str(nodes[-1].pk), "expected_version": 0},
            )
            self.assertEqual(response.status_code, 422, response.content)
            nodes[0].refresh_from_db()
            self.assertIsNone(nodes[0].parent_item_id)

    def test_parent_owner_deleted_and_promotion_reorder(self):
        foreign = Item.objects.create(owner=self.other, kind="text")
        deleted = Item.objects.create(
            owner=self.owner, kind="text", deleted_at=timezone.now()
        )
        for parent in (foreign, deleted):
            self.assertEqual(
                self.patch(
                    f"/items/{self.item.pk}/structure",
                    {"parent_item_id": str(parent.pk), "expected_version": 0},
                ).status_code,
                404,
            )
        parent = Item.objects.create(owner=self.owner, kind="text")
        self.assertEqual(
            self.patch(
                f"/items/{self.item.pk}/structure",
                {
                    "parent_item_id": str(parent.pk),
                    "sort_order": 42,
                    "expected_version": 0,
                },
            ).status_code,
            200,
        )
        self.assertEqual(
            self.patch(
                f"/items/{self.item.pk}/structure",
                {"parent_item_id": None, "sort_order": 9, "expected_version": 1},
            ).status_code,
            200,
        )
        self.item.refresh_from_db()
        self.assertIsNone(self.item.parent_item_id)
        self.assertEqual(self.item.outline_order, 9)

    def test_manual_group_deselect_clears_home_but_keeps_note(self):
        result = self.patch(f"/items/{self.item.pk}/organization", {"topic_ids": []})
        self.assertEqual(result.status_code, 200, result.content)
        self.item.refresh_from_db()
        self.assertIsNone(self.item.home_topic_id)
        self.assertEqual(self.item.structure_version, 1)
        self.assertEqual(self.item.note, "Tiếng Việt\r\n")

    def test_deleted_parent_does_not_hide_live_child(self):
        child = Item.objects.create(
            owner=self.owner, kind="text", parent_item=self.item, note="Còn nguyên"
        )
        self.item.deleted_at = timezone.now()
        self.item.save()
        results = self.client.get("/api/v1/explorer/children?unfiled=true").json()[
            "notes"
        ]
        self.assertIn(str(child.pk), [row["item_id"] for row in results])

    def test_initial_page_omits_note_body_and_is_stably_bounded(self):
        Item.objects.bulk_create(
            [
                Item(owner=self.owner, kind="text", note="PRIVATE BODY" * 1000)
                for _ in range(120)
            ]
        )
        pages = []
        offset = 0
        while offset is not None:
            response = self.client.get(
                f"/api/v1/explorer/children?offset={offset}&limit=50"
            )
            self.assertEqual(response.status_code, 200, response.content)
            data = response.json()
            self.assertTrue(
                all(
                    "note" not in row and len(row["title"]) <= 120
                    for row in data["notes"]
                )
            )
            self.assertLessEqual(len(data["notes"]), 50)
            pages.extend(row["item_id"] for row in data["notes"])
            offset = data["next_offset"]
        self.assertEqual(len(pages), 120)
        self.assertEqual(len(set(pages)), 120)

    def test_concurrent_reverse_parent_moves_never_store_cycle(self):
        peer = Item.objects.create(owner=self.owner, kind="text")
        barrier = Barrier(2)

        def move(pair):
            close_old_connections()
            try:
                client = Client()
                client.force_login(self.owner)
                barrier.wait(timeout=10)
                result = client.patch(
                    f"/api/v1/items/{pair[0]}/structure",
                    {"parent_item_id": str(pair[1]), "expected_version": 0},
                    content_type="application/json",
                )
                return result.status_code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(
                pool.map(move, [(self.item.pk, peer.pk), (peer.pk, self.item.pk)])
            )
        self.assertEqual(sorted(results), [200, 422])
        self.item.refresh_from_db()
        peer.refresh_from_db()
        self.assertFalse(
            self.item.parent_item_id == peer.pk and peer.parent_item_id == self.item.pk
        )

    @unittest.skipUnless(
        os.getenv("KT_EXPLORER_SCALE") == "1", "opt-in10000Item/1000folder QA benchmark"
    )
    def test_scale_ten_thousand_items_thousand_folders(self):
        folders = Topic.objects.bulk_create(
            [
                Topic(owner=self.owner, name=f"Folder {i}", sort_order=i)
                for i in range(1000)
            ]
        )
        notes = Item.objects.bulk_create(
            [
                Item(
                    owner=self.owner,
                    kind="text",
                    title=f"Note {i}",
                    note="Raw tiếng Việt" * 100,
                    home_topic=folders[i % 1000],
                )
                for i in range(10000)
            ]
        )
        ItemTopic.objects.bulk_create(
            [
                ItemTopic(item=item, topic=folders[i % 1000], user_pinned=True)
                for i, item in enumerate(notes)
            ]
        )
        samples = []
        queries = []
        for index in range(30):
            with CaptureQueriesContext(connection) as measured:
                started = time.perf_counter()
                page = explorer.children(
                    self.owner.pk, folder_id=folders[index % 1000].pk
                )
                samples.append((time.perf_counter() - started) * 1000)
            queries.append(len(measured))
            self.assertEqual(len(page["notes"]), 10)
        report = {
            "items": 10000,
            "folders": 1000,
            "samples": len(samples),
            "p95_ms": round(quantiles(samples, n=100, method="inclusive")[94], 3),
            "max_queries": max(queries),
            "note_bodies_in_initial_response": False,
        }
        print("KT122 scale " + json.dumps(report))
        self.assertLessEqual(max(queries), 5)
        self.assertEqual(len(tree(self.owner.pk)), 1001)
