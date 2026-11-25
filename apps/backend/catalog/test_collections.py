import json
import statistics
from datetime import UTC, datetime
from time import perf_counter

from config.session import session_api
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from ninja import NinjaAPI

from .api import router as item_router
from .collection_api import router
from .collection_models import SavedCollection
from .collection_service import CollectionQuery, matching_items
from .groups_api import router as groups_router
from .models import Item, ItemTag, ItemTopic, Tag, Topic

test_api = NinjaAPI(urls_namespace="kt125-test")
test_api.add_router("", router)
test_api.add_router("", groups_router)
test_api.add_router("", item_router)
urlpatterns = [path("api/v1/session", session_api), path("api/v1/", test_api.urls)]


@override_settings(ROOT_URLCONF=__name__)
class CollectionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="collection-owner")
        cls.other = get_user_model().objects.create_user(username="collection-other")
        cls.topics = [
            Topic.objects.create(owner=cls.owner, name=f"Nhóm {index}")
            for index in range(3)
        ]
        cls.tags = [
            Tag.objects.create(owner=cls.owner, name=f"Nhãn {index}")
            for index in range(3)
        ]
        cls.rows = [
            Item.objects.create(
                owner=cls.owner,
                kind="text",
                title=f"Bài {index}",
                note="Tri thức tiếng Việt",
                favorite=index % 2 == 0,
                saved_at=datetime(2026, 11, 20, 16 + index % 2, 30, tzinfo=UTC),
                published_at=datetime(2025, 2, 1, tzinfo=UTC),
                source_fetch="done" if index % 2 == 0 else "failed",
                content_extract="done",
            )
            for index in range(8)
        ]
        for index, item in enumerate(cls.rows):
            for bit in range(3):
                if index & (1 << bit):
                    ItemTopic.objects.create(
                        item=item, topic=cls.topics[bit], user_pinned=True
                    )
                    ItemTag.objects.create(
                        item=item, tag=cls.tags[bit], user_pinned=True
                    )
        cls.foreign = Topic.objects.create(owner=cls.other, name="Riêng tư")
        Item.objects.create(owner=cls.other, kind="text", note="Tri thức tiếng Việt")

    def setUp(self):
        self.client.force_login(self.owner)

    def post(self, data, path="/collections"):
        return self.client.post("/api/v1" + path, data, content_type="application/json")

    def test_thirty_boolean_and_timezone_combinations_match_independent_sets(self):
        cases = []
        for kind in ("topics", "tags"):
            values = getattr(self, kind)
            for any_bits, all_bits, excluded in (
                ([0], [], []),
                ([0, 1], [], []),
                ([], [0, 1], []),
                ([0, 1], [], [2]),
                ([], [], [0]),
                ([2], [1], [0]),
            ):
                for favorite in (None, True):
                    conditions = {
                        "any": [values[n].pk for n in any_bits],
                        "all": [values[n].pk for n in all_bits],
                        "exclude": [values[n].pk for n in excluded],
                    }
                    spec = {kind: conditions, "favorite": favorite}
                    expected = {
                        row.pk
                        for index, row in enumerate(self.rows)
                        if (not any_bits or any(index & (1 << n) for n in any_bits))
                        and all(index & (1 << n) for n in all_bits)
                        and not any(index & (1 << n) for n in excluded)
                        and (favorite is None or row.favorite == favorite)
                    }
                    cases.append((spec, expected))
        for zone, day, expected in (
            (
                "Asia/Ho_Chi_Minh",
                "2026-11-20",
                {row.pk for n, row in enumerate(self.rows) if n % 2 == 0},
            ),
            (
                "Asia/Ho_Chi_Minh",
                "2026-11-21",
                {row.pk for n, row in enumerate(self.rows) if n % 2 == 1},
            ),
            ("UTC", "2026-11-20", {row.pk for row in self.rows}),
            ("America/New_York", "2026-11-20", {row.pk for row in self.rows}),
            ("Asia/Tokyo", "2026-11-21", {row.pk for row in self.rows}),
            ("UTC", "2025-02-01", set()),
        ):
            cases.append(
                ({"timezone": zone, "received": {"from": day, "to": day}}, expected)
            )
        self.assertEqual(len(cases), 30)
        for spec, expected in cases:
            with self.subTest(spec=spec):
                query = CollectionQuery.model_validate(spec)
                actual = list(
                    matching_items(self.owner, query).values_list("id", flat=True)
                )
                self.assertEqual(set(actual), expected)
                self.assertEqual(len(actual), len(set(actual)))
                response = self.post({"query": spec}, "/collections/preview")
                self.assertEqual(response.status_code, 200, response.content)
                self.assertEqual(response.json()["count"], len(expected))
        published = self.post(
            {"query": {"published": {"from": "2025-02-01", "to": "2025-02-01"}}},
            "/collections/preview",
        )
        self.assertEqual(published.json()["count"], 8)

    def test_crud_persists_query_view_and_never_mutates_items_or_pinned_groups(self):
        before = (
            list(Item.objects.order_by("id").values()),
            list(ItemTopic.objects.order_by("id").values()),
        )
        saved = self.post(
            {
                "name": "  Kiến thức yêu thích ",
                "query": {"favorite": True},
                "view": "table",
            }
        )
        self.assertEqual(saved.status_code, 201, saved.content)
        value = saved.json()
        url = "/api/v1/collections/" + value["id"]
        self.assertEqual(value["name"], "Kiến thức yêu thích")
        self.assertEqual(self.client.get(url).json(), value)
        self.assertEqual(self.client.get(url + "/items").json()["count"], 4)
        changed = self.client.patch(
            url,
            {
                "name": value["name"],
                "query": {"favorite": False},
                "view": "card",
                "expected_version": 1,
            },
            content_type="application/json",
        )
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(changed.json()["version"], 2)
        stale = self.client.patch(
            url,
            {"name": "Stale", "query": {}, "view": "list", "expected_version": 1},
            content_type="application/json",
        )
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(self.client.get(url).json()["view"], "card")
        self.assertEqual(self.client.delete(url).status_code, 200)
        self.assertFalse(SavedCollection.objects.exists())
        self.assertEqual(
            (
                list(Item.objects.order_by("id").values()),
                list(ItemTopic.objects.order_by("id").values()),
            ),
            before,
        )

    def test_dynamic_membership_follows_note_and_tag_changes_without_snapshot(self):
        created = self.post(
            {
                "name": "Động",
                "query": {"q": "nghiên cứu", "tags": {"all": [self.tags[0].pk]}},
            }
        ).json()
        url = "/api/v1/collections/" + created["id"] + "/items"
        self.assertEqual(self.client.get(url).json()["count"], 0)
        item = self.rows[0]
        item.note = "Nghiên cứu tiếng Việt"
        item.save()
        ItemTag.objects.create(item=item, tag=self.tags[0])
        self.assertEqual(self.client.get(url).json()["count"], 1)
        ItemTag.objects.filter(item=item, tag=self.tags[0]).delete()
        self.assertEqual(self.client.get(url).json()["count"], 0)
        self.assertEqual(Item.objects.count(), 9)

    def test_auth_owner_csrf_deleted_archived_and_query_validation(self):
        value = self.post({"name": "Riêng"}).json()
        url = "/api/v1/collections/" + value["id"]
        self.client.force_login(self.other)
        for endpoint in (url, url + "/items"):
            self.assertEqual(self.client.get(endpoint).status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get("/api/v1/collections").status_code, 401)
        self.client.force_login(self.owner)
        for query in (
            {"sql": "DROP TABLE catalog_item"},
            {"sort": "id;drop"},
            {"timezone": "../bad"},
            {"tags": {"all": [True]}},
            {"topics": {"any": [self.foreign.pk]}},
            {"schema_version": 2},
            {"received": {"from": "2026-02-30"}},
            {"received": {"from": "2026-03-02", "to": "2026-03-01"}},
        ):
            with self.subTest(query=query):
                self.assertEqual(
                    self.post({"name": "Invalid", "query": query}).status_code, 422
                )
        denied = Client(enforce_csrf_checks=True)
        denied.force_login(self.owner)
        self.assertEqual(
            denied.post(
                "/api/v1/collections", {"name": "x"}, content_type="application/json"
            ).status_code,
            403,
        )
        item = self.rows[0]
        item.deleted_at = datetime.now(UTC)
        item.save()
        self.assertEqual(self.client.get(url + "/items").json()["count"], 7)
        self.topics[0].archived = True
        self.topics[0].save()
        self.assertEqual(
            self.post(
                {"name": "Archive", "query": {"topics": {"any": [self.topics[0].pk]}}}
            ).status_code,
            422,
        )

    def test_nfc_casefold_duplicate_and_preview_does_not_create(self):
        self.assertEqual(self.post({"name": "Tiếng Việt"}).status_code, 201)
        self.assertEqual(self.post({"name": "TIẾNG VIỆT"}).status_code, 409)
        before = SavedCollection.objects.count()
        self.assertEqual(
            self.post({"query": {}}, "/collections/preview").status_code, 200
        )
        self.assertEqual(SavedCollection.objects.count(), before)

    def test_source_status_matches_note_only_summary_and_published_nulls_last(self):
        for key, status in (
            ("source_fetch", "not_applicable"),
            ("content_extract", "not_available"),
        ):
            self.assertEqual(
                self.post({"query": {key: status}}, "/collections/preview").json()[
                    "count"
                ],
                8,
            )
            self.assertEqual(
                self.post({"query": {key: "done"}}, "/collections/preview").json()[
                    "count"
                ],
                0,
            )
        row = self.rows[0]
        row.published_at = None
        row.save()
        ordered = list(
            matching_items(
                self.owner, CollectionQuery(sort="published_desc")
            ).values_list("id", flat=True)
        )
        self.assertEqual(ordered[-1], row.pk)


@override_settings(ROOT_URLCONF=__name__)
class CollectionScaleTests(TestCase):
    def test_ten_thousand_items_hundred_groups_five_queries_paginate_stably(self):
        owner = get_user_model().objects.create_user(username="scale-collection")
        other = get_user_model().objects.create_user(username="scale-other")
        groups = Topic.objects.bulk_create(
            [Topic(owner=owner, name=f"Kho {n}") for n in range(100)]
        )
        rows = Item.objects.bulk_create(
            [
                Item(
                    owner=owner,
                    kind="text",
                    title=f"Bài {n:05}",
                    note="Nội dung chuẩn",
                    favorite=n % 5 == 0,
                    saved_at=datetime(2026, 11, 20, tzinfo=UTC),
                )
                for n in range(10_000)
            ],
            batch_size=1000,
        )
        ItemTopic.objects.bulk_create(
            [
                ItemTopic(item=row, topic=groups[n % 100], user_pinned=True)
                for n, row in enumerate(rows)
            ],
            batch_size=1000,
        )
        Item.objects.create(owner=other, kind="text", note="Riêng tư")
        # A TestCase bulk load is uncommitted and autovacuum cannot update its
        # statistics. Analyze the synthetic fixture before measuring plans.
        with connection.cursor() as cursor:
            for table in (
                "catalog_item",
                "catalog_topic",
                "catalog_itemtopic",
                "processing_derivedcontent",
            ):
                cursor.execute("ANALYZE " + table)
        definitions = [
            {},
            {"favorite": True},
            {"topics": {"any": [groups[0].pk, groups[1].pk]}},
            {"topics": {"exclude": [groups[0].pk]}},
            {"q": "nội dung chuẩn", "favorite": False},
        ]
        self.client.force_login(owner)
        samples, query_counts = [], []
        for index, definition in enumerate(definitions):
            created = self.client.post(
                "/api/v1/collections",
                {"name": f"Bộ lọc {index}", "query": definition, "view": "list"},
                content_type="application/json",
            )
            self.assertEqual(created.status_code, 201)
            value = created.json()
            expected = list(
                matching_items(
                    owner, CollectionQuery.model_validate(definition)
                ).values_list("id", flat=True)
            )
            actual, offset = [], 0
            while offset is not None:
                started = perf_counter()
                with CaptureQueriesContext(connection) as queries:
                    response = self.client.get(
                        f"/api/v1/collections/{value['id']}/items?limit=100&offset={offset}"
                    )
                    payload = response.json()
                samples.append((perf_counter() - started) * 1000)
                query_counts.append(len(queries))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(payload["count"], len(expected))
                actual.extend(row["item_id"] for row in payload["results"])
                offset = payload["next_offset"]
            self.assertEqual(actual, list(map(str, expected)))
            self.assertEqual(len(actual), len(set(actual)))
        ordered = sorted(samples)
        p95 = ordered[max(0, __import__("math").ceil(len(ordered) * 0.95) - 1)]
        print(
            "KT125 scale: "
            + json.dumps(
                {
                    "items": 10000,
                    "groups": 100,
                    "queries": 5,
                    "samples": len(samples),
                    "p95_ms": round(p95, 2),
                    "median_ms": round(statistics.median(samples), 2),
                    "max_query_count_per_http_page": max(query_counts),
                    "scope": "synthetic local PostgreSQL HTTP testclient",
                }
            )
        )
        self.assertEqual(Item.objects.count(), 10001)
        self.assertEqual(SavedCollection.objects.count(), 5)
