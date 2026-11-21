"""P04 regression matrix for folder placements, unfiled and mixed pages.

Run on PostgreSQL: python manage.py test catalog.test_parallel_home_p04
Optional large fixture: P04_SCALE=1 python manage.py test catalog.test_parallel_home_p04
"""
import os
import unittest

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from . import explorer
from .models import Item, ItemTopic, Topic


class ParallelHomeP04Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.owner = users.create_user(username="p04-owner")
        cls.other = users.create_user(username="p04-other")

    def setUp(self):
        self.client.force_login(self.owner)

    def folder(self, name, *, parent=None, owner=None, archived=False, sort=0):
        return Topic.objects.create(
            owner=owner or self.owner,
            name=name,
            parent=parent,
            archived=archived,
            sort_order=sort,
        )

    def note(self, *, title="", home=None, parent=None, owner=None, deleted=False):
        return Item.objects.create(
            owner=owner or self.owner,
            kind=Item.Kind.TEXT,
            title=title,
            note="SYNTHETIC P04 BODY",
            home_topic=home,
            parent_item=parent,
            deleted_at=timezone.now() if deleted else None,
        )

    def assign(self, item, folder):
        return ItemTopic.objects.create(
            item=item, topic=folder, origin="user", user_pinned=True
        )

    def catalog_unfiled(self):
        response = self.client.get("/api/v1/items", {"unfiled": "true"})
        self.assertEqual(response.status_code, 200, response.content)
        return {row["item_id"] for row in response.json()["results"]}

    def explorer_unfiled(self):
        response = self.client.get("/api/v1/explorer/children", {"unfiled": "true"})
        self.assertEqual(response.status_code, 200, response.content)
        return {row["item_id"] for row in response.json()["notes"]}

    def test_unfiled_matrix_matches_library_and_explorer(self):
        active = self.folder("Active")
        archived = self.folder("Archived", archived=True)
        foreign = self.folder("Foreign", owner=self.other)
        parent = self.note(title="parent", home=active)
        self.assign(parent, active)
        examples = [
            ("plain", {}, True),
            ("parented-without-folder", {"parent": parent}, True),
            ("active-home", {"home": active}, False),
            ("archived-home", {"home": archived}, True),
            ("home-and-parent", {"home": active, "parent": parent}, False),
            ("archive-and-parent", {"home": archived, "parent": parent}, True),
            ("deleted", {"deleted": True}, False),
            ("foreign-owner", {"owner": self.other}, False),
            ("foreign-home-legacy", {"home": foreign}, True),
            ("active-home-deleted", {"home": active, "deleted": True}, False),
        ]
        expected = set()
        created = {}
        for label, kwargs, is_unfiled in examples:
            with self.subTest(label=label):
                item = self.note(title=label, **kwargs)
                created[label] = item
                if is_unfiled:
                    expected.add(str(item.pk))
        membership_cases = [
            ("only-active-membership", active, False),
            ("only-archived-membership", archived, True),
            ("active-and-archived", active, False),
            ("parent-with-active-shortcut", active, False),
        ]
        for label, folder, is_unfiled in membership_cases:
            with self.subTest(label=label):
                item = self.note(
                    title=label,
                    parent=parent if label.startswith("parent-") else None,
                )
                self.assign(item, folder)
                if label == "active-and-archived":
                    self.assign(item, archived)
                if is_unfiled:
                    expected.add(str(item.pk))
        self.assertEqual(self.catalog_unfiled(), expected)
        self.assertEqual(self.explorer_unfiled(), expected)
        # Folderless structural children are still genuinely unfiled.
        self.assertIn(str(created["parented-without-folder"].pk), expected)

    def test_home_only_and_shortcuts_are_visible_once_with_distinct_counts(self):
        target = self.folder("A")
        other = self.folder("B")
        home_only = self.note(title="home-only", home=target)
        shared = self.note(title="shared", home=target)
        self.assign(shared, target)
        self.assign(shared, other)
        membership_only = self.note(title="membership-only")
        self.assign(membership_only, target)
        archived = self.note(title="archived", home=target, deleted=True)
        self.assign(archived, target)
        foreign = self.note(owner=self.other)
        self.assign(foreign, target)  # legacy inconsistent edge may not leak
        results = self.client.get(
            "/api/v1/explorer/children", {"folder_id": target.pk}
        )
        self.assertEqual(results.status_code, 200)
        rows = results.json()["notes"]
        self.assertEqual(
            {r["item_id"] for r in rows},
            {str(home_only.pk), str(shared.pk), str(membership_only.pk)},
        )
        self.assertEqual(len(rows), 3)
        root = self.client.get("/api/v1/explorer/children").json()
        folder_row = next(row for row in root["folders"] if row["id"] == target.pk)
        self.assertEqual(folder_row["direct_count"], 3)
        other_page = self.client.get(
            "/api/v1/explorer/children", {"folder_id": other.pk}
        ).json()
        self.assertEqual(other_page["notes"][0]["item_id"], str(shared.pk))
        self.assertTrue(other_page["notes"][0]["shortcut"])
        self.assertNotIn(str(foreign.pk), {row["item_id"] for row in rows})

    def test_mixed_pagination_is_one_stream_without_duplicates(self):
        root_folders = [
            self.folder(f"F-{i:02d}", sort=i) for i in range(17)
        ]
        notes = [self.note(title=f"N-{i:02d}") for i in range(23)]
        observed_folders, observed_notes = [], []
        offset = 0
        while offset is not None:
            response = self.client.get(
                "/api/v1/explorer/children", {"limit": 7, "offset": offset}
            )
            self.assertEqual(response.status_code, 200, response.content)
            page = response.json()
            self.assertLessEqual(len(page["folders"]) + len(page["notes"]), 7)
            observed_folders.extend(row["id"] for row in page["folders"])
            observed_notes.extend(row["item_id"] for row in page["notes"])
            next_offset = page["next_offset"]
            if next_offset is not None:
                self.assertGreater(next_offset, offset)
            offset = next_offset
        self.assertEqual(
            observed_folders, [folder.pk for folder in root_folders]
        )
        self.assertEqual(set(observed_notes), {str(n.pk) for n in notes})
        self.assertEqual(len(observed_notes), len(set(observed_notes)))
        self.assertEqual(len(observed_folders), len(set(observed_folders)))
        for limit in (1, 2, 7, 17, 20, 40, 100):
            with self.subTest(limit=limit):
                page = explorer.children(self.owner.pk, limit=limit)
                self.assertLessEqual(
                    len(page["notes"]) + len(page["folders"]), limit
                )

    def test_page_boundary_exact_folders_then_notes(self):
        self.folder("first")
        self.folder("second")
        item = self.note()
        first = explorer.children(self.owner.pk, limit=2)
        self.assertEqual(len(first["folders"]), 2)
        self.assertEqual(len(first["notes"]), 0)
        self.assertEqual(first["next_offset"], 2)
        second = explorer.children(self.owner.pk, limit=2, offset=2)
        self.assertEqual([r["item_id"] for r in second["notes"]], [str(item.pk)])
        self.assertIsNone(second["next_offset"])
        self.assertEqual(
            explorer.children(self.owner.pk, limit=2, offset=500)["notes"], []
        )

    def test_owner_archived_deleted_parent_and_invalid_scope(self):
        active = self.folder("A")
        archived = self.folder("Gone", archived=True)
        foreign = self.folder("Private", owner=self.other)
        own = self.note(home=active)
        other_note = self.note(owner=self.other)
        for folder in (archived, foreign):
            with self.subTest(folder=folder.pk):
                response = self.client.get(
                    "/api/v1/explorer/children", {"folder_id": folder.pk}
                )
                self.assertEqual(response.status_code, 404)
        for params in (
            {"folder_id": active.pk, "unfiled": "true"},
            {"parent_item_id": str(own.pk), "unfiled": "true"},
            {"folder_id": active.pk, "parent_item_id": str(own.pk)},
        ):
            with self.subTest(params=params):
                response = self.client.get("/api/v1/explorer/children", params)
                self.assertEqual(response.status_code, 422)
        response = self.client.get(
            "/api/v1/explorer/children", {"parent_item_id": str(other_note.pk)}
        )
        self.assertEqual(response.status_code, 404)
        own.deleted_at = timezone.now()
        own.save()
        response = self.client.get(
            "/api/v1/explorer/children", {"parent_item_id": str(own.pk)}
        )
        self.assertEqual(response.status_code, 404)

    def test_move_version_and_pinned_memberships_remain_intact(self):
        a, b, c = [self.folder(f"Move {name}") for name in ("A", "B", "C")]
        note = self.note(home=a)
        self.assign(note, a)
        self.assign(note, b)
        response = self.client.patch(
            f"/api/v1/items/{note.pk}/placement",
            {"action": "move", "folder_id": c.pk, "expected_version": 0},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        note.refresh_from_db()
        self.assertEqual(note.home_topic_id, c.pk)
        self.assertEqual(
            set(ItemTopic.objects.filter(item=note).values_list("topic_id", flat=True)),
            {a.pk, b.pk, c.pk},
        )
        self.assertTrue(
            all(row.user_pinned for row in ItemTopic.objects.filter(item=note))
        )
        stale = self.client.patch(
            f"/api/v1/items/{note.pk}/placement",
            {"action": "move", "folder_id": a.pk, "expected_version": 0},
            content_type="application/json",
        )
        self.assertEqual(stale.status_code, 409)
        note.refresh_from_db()
        self.assertEqual(note.home_topic_id, c.pk)

    @unittest.skipUnless(os.environ.get("P04_SCALE") == "1", "opt-in PostgreSQL 10k fixture")
    def test_ten_thousand_item_paging_fixture(self):
        folder = self.folder("Bulk")
        Item.objects.bulk_create([
            Item(owner=self.owner, kind=Item.Kind.TEXT, title=f"bulk-{i}")
            for i in range(10000)
        ], batch_size=500)
        ids = set()
        for offset in range(0, 10000, 100):
            page = explorer.children(self.owner.pk, limit=100, offset=offset + 1)
            ids.update(row["item_id"] for row in page["notes"])
        self.assertEqual(len(ids), 10000)
        self.assertEqual(folder.pk, explorer.children(self.owner.pk, limit=1)["folders"][0]["id"])
