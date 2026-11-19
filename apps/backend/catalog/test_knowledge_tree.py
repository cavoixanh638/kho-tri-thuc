from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone
from processing.knowledge import snapshot

from .knowledge_tree import TreeError, descendants, save_node, tree
from .models import Item, ItemTopic, Topic


class KnowledgeTreeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="tree-owner")
        cls.other = get_user_model().objects.create_user(username="tree-other")

    def setUp(self):
        self.client.force_login(self.owner)

    def node(self, name, parent=None, kind="folder", owner=None, **extra):
        result, _ = save_node(
            (owner or self.owner).pk,
            name=name,
            parent_id=parent.pk if parent else None,
            node_kind=kind,
            **extra,
        )
        return result

    def article(self, title, *nodes, owner=None, deleted=False):
        item = Item.objects.create(
            owner=owner or self.owner,
            kind="text",
            title=title,
            note="Nội dung " + title,
            deleted_at=timezone.now() if deleted else None,
        )
        for node in nodes:
            ItemTopic.objects.create(item=item, topic=node, user_pinned=True)
        return item

    def test_descendant_counts_and_library_filter_deduplicate_articles_in_multiple_branches(
        self,
    ):
        root = self.node("Kho khoa học", kind="library")
        field = self.node("Kỹ thuật", root, "field")
        series = self.node("Bộ sách", field, "series")
        book = self.node("Sách thứ nhất", series, "book")
        chapter = self.node("Chương một", book, "chapter")
        peer = self.node("Kho khác", kind="library")
        shared = self.article("Một bài nhiều nhánh", field, chapter)
        leaf = self.article("Bài ở lá", chapter)
        self.article("Bài đã xóa", chapter, deleted=True)
        outside = self.article("Bài ở kho khác", peer)
        unfiled = self.article("Chưa vào mục lục")
        foreign_node = self.node("Kho riêng", owner=self.other)
        self.article("Dữ liệu tài khoản khác", chapter, owner=self.other)

        data = {row["id"]: row for row in tree(self.owner.pk)}
        self.assertEqual(data[root.pk]["item_count"], 2)
        self.assertEqual(data[field.pk]["direct_count"], 1)
        self.assertEqual(data[chapter.pk]["direct_count"], 2)
        self.assertEqual(data[chapter.pk]["depth"], 4)
        self.assertEqual(
            data[chapter.pk]["path_ids"],
            [root.pk, field.pk, series.pk, book.pk, chapter.pk],
        )
        self.assertEqual(
            data[chapter.pk]["path"],
            "Kho khoa học / Kỹ thuật / Bộ sách / Sách thứ nhất / Chương một",
        )
        self.assertNotIn(foreign_node.pk, data)
        self.assertEqual(
            descendants(self.owner.pk, root.pk),
            {root.pk, field.pk, series.pk, book.pk, chapter.pk},
        )

        response = self.client.get("/api/v1/items", {"node_id": root.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {row["item_id"] for row in response.json()["results"]},
            {str(shared.pk), str(leaf.pk)},
        )
        self.assertEqual(len(response.json()["results"]), 2)
        response = self.client.get("/api/v1/items", {"unfiled": "true"})
        self.assertEqual(
            {row["item_id"] for row in response.json()["results"]}, {str(unfiled.pk)}
        )
        response = self.client.get("/api/v1/items", {"node_id": peer.pk})
        self.assertEqual(
            [row["item_id"] for row in response.json()["results"]], [str(outside.pk)]
        )

    def test_cycle_foreign_parent_and_archived_parent_are_rejected_without_mutation(
        self,
    ):
        root = self.node("Gốc", kind="library")
        child = self.node("Con", root)
        leaf = self.node("Lá", child)
        foreign = self.node("Riêng", owner=self.other)
        archived = Topic.objects.create(
            owner=self.owner, name="Đã lưu trữ", archived=True
        )
        for parent_id, error in (
            (root.pk, "knowledge_tree_cycle"),
            (leaf.pk, "knowledge_tree_cycle"),
            (foreign.pk, "unknown_parent_node"),
            (archived.pk, "unknown_parent_node"),
        ):
            with (
                self.subTest(parent_id=parent_id),
                self.assertRaisesRegex(TreeError, error),
            ):
                save_node(
                    self.owner.pk,
                    node_id=root.pk,
                    name="Gốc",
                    parent_id=parent_id,
                    node_kind="library",
                )
            root.refresh_from_db()
            self.assertIsNone(root.parent_id)
        self.assertEqual(
            self.client.get("/api/v1/items", {"node_id": foreign.pk}).status_code, 404
        )
        self.assertEqual(
            self.client.patch(
                f"/api/v1/knowledge-tree/{foreign.pk}",
                {"name": "Không được sửa"},
                content_type="application/json",
            ).status_code,
            404,
        )

    def test_rename_and_move_update_group_paths_and_export_without_copying_article(
        self,
    ):
        root = self.node("Công nghệ", kind="library")
        other_root = self.node("Tham khảo", kind="library")
        book = self.node("Cẩm nang", root, "book")
        chapter = self.node("Chương an toàn", book, "chapter")
        article = self.article("Giao dịch", chapter)
        first = snapshot(article.pk)
        save_node(
            self.owner.pk,
            node_id=book.pk,
            name="Sách vận hành",
            parent_id=other_root.pk,
            node_kind="book",
        )
        second = snapshot(article.pk)
        self.assertNotEqual(first.version, second.version)
        expected = "Tham khảo / Sách vận hành / Chương an toàn"
        self.assertIn(expected, second.body.decode())
        self.assertNotIn("Công nghệ / Cẩm nang", second.body.decode())
        groups = self.client.get("/api/v1/groups").json()["topics"]
        self.assertEqual(
            next(row["path"] for row in groups if row["id"] == chapter.pk), expected
        )
        organization = self.client.get(
            f"/api/v1/items/{article.pk}/organization"
        ).json()
        self.assertEqual(organization["topics"][0]["path"], expected)
        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(ItemTopic.objects.get(item=article).topic_id, chapter.pk)
        self.assertEqual(
            self.client.get("/api/v1/items", {"node_id": root.pk}).json()["results"], []
        )
        self.assertEqual(
            len(
                self.client.get("/api/v1/items", {"node_id": other_root.pk}).json()[
                    "results"
                ]
            ),
            1,
        )

    def test_sibling_name_normalization_is_idempotent_and_same_leaf_names_can_exist_elsewhere(
        self,
    ):
        root = self.node("Gốc")
        peer = self.node("Gốc khác")
        first = self.node("Vận hành", root)
        repeated, created = save_node(
            self.owner.pk, name=" VẬN HÀNH ", parent_id=root.pk, node_kind="folder"
        )
        self.assertFalse(created)
        self.assertEqual(repeated.pk, first.pk)
        self.assertNotEqual(self.node("Vận hành", peer).pk, first.pk)
        another = self.node("Khác", root)
        with self.assertRaisesRegex(TreeError, "knowledge_name_exists"):
            save_node(
                self.owner.pk,
                node_id=another.pk,
                name="Vận hành",
                parent_id=root.pk,
                node_kind="folder",
            )

    def test_tree_api_creation_replays_and_requires_session_csrf_and_owner_scope(self):
        body = {
            "name": "Kho con",
            "parent_id": None,
            "node_kind": "library",
            "sort_order": 2,
        }
        reply = self.client.post(
            "/api/v1/knowledge-tree", body, content_type="application/json"
        )
        self.assertEqual(reply.status_code, 201)
        node_id = reply.json()["id"]
        self.assertEqual(reply.json()["path"], "Kho con")
        self.assertEqual(
            self.client.post(
                "/api/v1/knowledge-tree", body, content_type="application/json"
            ).status_code,
            200,
        )
        child = self.client.post(
            "/api/v1/knowledge-tree",
            {**body, "name": "Lĩnh vực", "parent_id": node_id, "node_kind": "field"},
            content_type="application/json",
        )
        self.assertEqual(child.status_code, 201)
        moved = self.client.patch(
            f"/api/v1/knowledge-tree/{child.json()['id']}",
            {**body, "name": "Lĩnh vực đã đổi", "node_kind": "field"},
            content_type="application/json",
        )
        self.assertEqual(moved.status_code, 200)
        self.assertEqual(moved.json()["depth"], 0)
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(self.owner)
        self.assertEqual(
            csrf.post(
                "/api/v1/knowledge-tree", body, content_type="application/json"
            ).status_code,
            403,
        )
        self.client.force_login(self.other)
        self.assertEqual(self.client.get("/api/v1/knowledge-tree").json()["nodes"], [])
        self.client.logout()
        self.assertEqual(self.client.get("/api/v1/knowledge-tree").status_code, 401)
