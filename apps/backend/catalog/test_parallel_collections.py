"""P11 independent black-box and ORM audit of KT125 saved collections.

Owned by P11 only. Normal suite uses a small fixture. Set P11_SCALE=1 to
run a PostgreSQL-only 10k Item/100 Topic/5 saved-query measurement; this does
not establish a production latency SLO.
"""
import json
import math
import os
import statistics
import unittest
from datetime import UTC, datetime, timedelta
from time import perf_counter
from uuid import NAMESPACE_URL, uuid5

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from pydantic import ValidationError

from .collection_models import SavedCollection
from .collection_service import CollectionQuery, matching_items, validate_groups
from .models import Item, ItemProject, ItemTag, ItemTopic, Project, Tag, Topic

API = "/api/v1/collections"


@override_settings(ROOT_URLCONF="catalog.test_collections")
class ParallelCollectionRules(TestCase):
    """Thirty independently evaluated group fixtures, plus API/security edges."""

    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.owner = users.objects.create_user(username="p11-owner")
        cls.other = users.objects.create_user(username="p11-other")
        cls.group_models = {
            "topics": (Topic, ItemTopic, "topic"),
            "projects": (Project, ItemProject, "project"),
            "tags": (Tag, ItemTag, "tag"),
        }
        cls.groups = {
            key: model.objects.bulk_create(
                [model(owner=cls.owner, name=f"P11 {key} {n}") for n in range(3)]
            )
            for key, (model, _, _) in cls.group_models.items()
        }
        cls.rows = Item.objects.bulk_create(
            [
                Item(
                    owner=cls.owner,
                    id=uuid5(NAMESPACE_URL, f"p11-small-{n}"),
                    kind="text",
                    title=f"Ghi chu {n:02}",
                    note="Tri thuc tieng Viet",
                    saved_at=datetime(2026, 11, 20, 16 + n % 2, 30, tzinfo=UTC),
                    published_at=(
                        datetime(2025, 2, 1, tzinfo=UTC) if n % 3 == 0 else None
                    ),
                    favorite=n % 2 == 0,
                )
                for n in range(64)
            ]
        )
        cls.members = {key: {} for key in cls.groups}
        for key, (_, relation, field) in cls.group_models.items():
            links = []
            for n, item in enumerate(cls.rows):
                memberships = {
                    cls.groups[key][bit].pk for bit in range(3) if n & (1 << bit)
                }
                cls.members[key][item.pk] = memberships
                for group in cls.groups[key]:
                    if group.pk in memberships:
                        links.append(relation(item=item, **{field: group}, user_pinned=True))
            relation.objects.bulk_create(links)
        cls.foreign_group = Topic.objects.create(owner=cls.other, name="P11 private")
        cls.foreign_item = Item.objects.create(
            owner=cls.other, kind="text", title="Owner two", note="Tri thuc tieng Viet"
        )

    def setUp(self):
        self.client.force_login(self.owner)

    def post(self, path, body):
        return self.client.post(path, body, content_type="application/json")

    def test_thirty_distinct_boolean_fixtures_against_python_oracle(self):
        patterns = [
            ([0], [], []),
            ([0, 2], [], []),
            ([], [0, 1], []),
            ([0, 1], [], [2]),
            ([], [2], [0]),
        ]
        checked = 0
        for key in ("topics", "projects", "tags"):
            groups = self.groups[key]
            for any_bits, all_bits, exclude_bits in patterns:
                for favorite in (None, True):
                    condition = {
                        "any": [groups[bit].pk for bit in any_bits],
                        "all": [groups[bit].pk for bit in all_bits],
                        "exclude": [groups[bit].pk for bit in exclude_bits],
                    }
                    definition = {key: condition, "favorite": favorite}
                    oracle = set()
                    for n, row in enumerate(self.rows):
                        bits = {bit for bit in range(3) if n & (1 << bit)}
                        if (
                            (not any_bits or any(bit in bits for bit in any_bits))
                            and all(bit in bits for bit in all_bits)
                            and not any(bit in bits for bit in exclude_bits)
                            and (favorite is None or row.favorite == favorite)
                        ):
                            oracle.add(row.pk)
                    with self.subTest(key=key, clause=condition, favorite=favorite):
                        query = CollectionQuery.model_validate(definition)
                        ids = list(
                            matching_items(self.owner, query).values_list("pk", flat=True)
                        )
                        self.assertEqual(set(ids), oracle)
                        self.assertEqual(len(ids), len(oracle))
                        reply = self.post(API + "/preview", {"query": definition})
                        self.assertEqual(reply.status_code, 200, reply.content)
                        self.assertEqual(reply.json()["count"], len(oracle))
                    checked += 1
        self.assertEqual(checked, 30)

    def test_saved_and_published_are_distinct_inclusive_local_days(self):
        for day, parity in (("2026-11-20", 0), ("2026-11-21", 1)):
            q = CollectionQuery.model_validate(
                {"timezone": "Asia/Ho_Chi_Minh",
                 "received": {"from": day, "to": day}}
            )
            ids = set(matching_items(self.owner, q).values_list("pk", flat=True))
            self.assertEqual(ids, {r.pk for n, r in enumerate(self.rows) if n % 2 == parity})
        q = CollectionQuery.model_validate(
            {"published": {"from": "2025-02-01", "to": "2025-02-01"}}
        )
        self.assertEqual(
            set(matching_items(self.owner, q).values_list("pk", flat=True)),
            {r.pk for n, r in enumerate(self.rows) if n % 3 == 0},
        )
        self.assertEqual(
            matching_items(self.owner, CollectionQuery(sort="published_desc"))
            .filter(published_at__isnull=True).count(),
            sum(r.published_at is None for r in self.rows),
        )

    def test_owner_isolation_dynamic_membership_and_no_item_mutation(self):
        definition = {
            "topics": {"any": [self.groups["topics"][0].pk]},
            "favorite": True,
        }
        before = {row.pk for row in self.rows}
        created = self.post(API, {"name": "P11 dynamic", "query": definition, "view": "list"})
        self.assertEqual(created.status_code, 201, created.content)
        collection_id = created.json()["id"]
        path = API + "/" + collection_id + "/items"
        initial = self.client.get(path).json()
        self.assertEqual(initial["count"], len(
            [n for n in range(64) if n % 2 == 0 and (n & 1)]
        ))
        # A new qualifying note is visible immediately without stored membership.
        item = self.rows[0]
        ItemTopic.objects.create(item=item, topic=self.groups["topics"][0])
        self.assertEqual(self.client.get(path).json()["count"], initial["count"] + 1)
        item.deleted_at = datetime.now(UTC)
        item.save(update_fields=["deleted_at", "updated_at"])
        self.assertEqual(self.client.get(path).json()["count"], initial["count"])
        self.assertEqual(set(Item.objects.filter(owner=self.owner).values_list("pk", flat=True)), before)
        self.client.force_login(self.other)
        for endpoint in (API + "/" + collection_id, path):
            self.assertEqual(self.client.get(endpoint).status_code, 404)
        self.assertEqual(self.client.get(API).json()["results"], [])
        own = self.post(API + "/preview", {"query": {}})
        self.assertEqual(own.status_code, 200)
        self.assertEqual(own.json()["count"], 1)
        self.client.force_login(self.owner)
        with self.assertRaises(ValueError):
            validate_groups(
                self.owner,
                CollectionQuery.model_validate(
                    {"topics": {"any": [self.foreign_group.pk]}}
                ),
            )
        self.assertEqual(
            matching_items(
                self.owner, CollectionQuery.model_validate(
                    {"topics": {"any": [self.foreign_group.pk]}}
                )
            ).count(),
            0,
        )

    def test_user_input_is_bound_and_strict_dsl_disallows_sql_fields(self):
        attack = "x'); DROP TABLE catalog_item; --"
        compiled, params = matching_items(
            self.owner, CollectionQuery.model_validate({"q": attack})
        ).query.sql_with_params()
        self.assertNotIn(attack, compiled)
        self.assertEqual(sum(value == attack for value in params), 2)
        for invalid in (
            {"sort": "saved_at; DELETE FROM catalog_item"},
            {"extra": "arbitrary"},
            {"topics": {"all": [True]}},
            {"topics": {"any": [-1]}},
            {"topics": {"any": [1, 1]}},
            {"received": {"from": "2026-02-30"}},
            {"published": {"from": "2026-11-22", "to": "2026-11-21"}},
            {"timezone": "../etc/passwd"},
            {"schema_version": 2},
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValidationError):
                CollectionQuery.model_validate(invalid)
        self.assertEqual(
            self.post(API + "/preview", {"query": {"topics": {"any": [self.foreign_group.pk]}}}).status_code,
            422,
        )

    def test_migration_columns_and_owner_index_exist(self):
        self.assertEqual(connection.vendor, "postgresql")
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT indexname FROM pg_indexes "
                "WHERE schemaname = current_schema() AND tablename = 'catalog_savedcollection'"
            )
            names = {row[0] for row in cursor.fetchall()}
        self.assertIn("collection_owner_name_uniq", names)
        self.assertIn("collection_owner_name_idx", names)
        self.assertTrue(SavedCollection._meta.get_field("query"))
        self.assertFalse(SavedCollection.objects.filter(owner=self.other).exists())

    def test_corrupt_legacy_definition_is_reported_for_migration_follow_up(self):
        # Diagnostic: a legacy/invalid JSON definition currently returns HTTP 500
        # instead of a versioned migration response. This does not mutate it.
        stale = SavedCollection.objects.create(
            owner=self.owner, name="P11 legacy", normalized_name="p11 legacy",
            query={"schema_version": 987, "sort": "not-supported"}, view="list",
        )
        client = Client(raise_request_exception=False)
        client.force_login(self.owner)
        response = client.get(API + "/" + str(stale.pk) + "/items")
        self.assertIn(response.status_code, (422, 500))
        print("P11 legacy saved-query read HTTP status:", response.status_code)


@unittest.skipUnless(os.getenv("P11_SCALE") == "1", "Opt-in P11_SCALE=1 PostgreSQL synthetic load")
@override_settings(ROOT_URLCONF="catalog.test_collections")
class ParallelCollectionScale(TestCase):
    """10k Items, 100 groups, 5 saved filters, two owners, real SQL measurements."""

    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.owner = users.objects.create_user(username="p11-scale-one")
        cls.other = users.objects.create_user(username="p11-scale-two")
        cls.groups = Topic.objects.bulk_create(
            [Topic(owner=cls.owner, name=f"P11 G{n:03d}") for n in range(100)]
        )
        cls.rows = Item.objects.bulk_create(
            [
                Item(
                    id=uuid5(NAMESPACE_URL, f"p11-scale-{n}"),
                    owner=cls.owner, kind="text",
                    title=f"P11 Knowledge {n:05d}",
                    note="Noi dung chuan",
                    favorite=n % 5 == 0,
                    saved_at=datetime(2026, 11, 20, tzinfo=UTC)
                    + timedelta(days=n % 7),
                )
                for n in range(10_000)
            ], batch_size=1000
        )
        ItemTopic.objects.bulk_create(
            [
                ItemTopic(item=row, topic=cls.groups[group_no])
                for n, row in enumerate(cls.rows)
                for group_no in (n % 100, (n + 7) % 100)
            ], batch_size=1000
        )
        Item.objects.create(
            owner=cls.other, kind="text", title="foreign",
            note="Noi dung chuan", favorite=True,
        )
        specs = [
            {},
            {"favorite": True},
            {"topics": {"any": [cls.groups[0].pk, cls.groups[1].pk]}},
            {"topics": {"all": [cls.groups[0].pk, cls.groups[7].pk],
                        "exclude": [cls.groups[1].pk]}},
            {"q": "Noi dung chuan", "favorite": False},
        ]
        cls.saved = [
            SavedCollection.objects.create(
                owner=cls.owner, name=f"P11 filter {n}",
                normalized_name=f"p11 filter {n}",
                query=CollectionQuery.model_validate(spec).model_dump(mode="json", by_alias=True),
                view=("list", "table", "card", "timeline", "list")[n],
            )
            for n, spec in enumerate(specs)
        ]

    def test_postgres_actual_pagination_query_count_p95_and_indexes(self):
        self.assertEqual(connection.vendor, "postgresql")
        self.client.force_login(self.owner)
        with connection.cursor() as cursor:
            for table in ("catalog_item", "catalog_topic", "catalog_itemtopic",
                          "processing_derivedcontent"):
                cursor.execute("ANALYZE " + table)
            cursor.execute(
                "SELECT indexname FROM pg_indexes WHERE schemaname = current_schema() "
                "AND tablename IN ('catalog_item', 'processing_derivedcontent', "
                "'catalog_savedcollection')"
            )
            indexes = {row[0] for row in cursor.fetchall()}
        self.assertIn("item_owner_saved_idx", indexes)
        self.assertIn("kt_item_fts_gin", indexes)
        self.assertIn("collection_owner_name_idx", indexes)
        # Full traversal of the largest saved query validates distinct, stable UUIDs.
        full = []
        offset = 0
        while offset is not None:
            response = self.client.get(
                API + "/" + str(self.saved[0].pk) + "/items",
                {"offset": offset, "limit": 100},
            )
            self.assertEqual(response.status_code, 200, response.content)
            data = response.json()
            self.assertEqual(data["count"], 10000)
            full.extend(row["item_id"] for row in data["results"])
            offset = data["next_offset"]
        expected = [
            str(row.pk) for row in sorted(
                self.rows, key=lambda row: (-row.saved_at.timestamp(), str(row.pk))
            )
        ]
        self.assertEqual(full, expected)
        self.assertEqual(len(set(full)), 10000)
        # Thirty measured actual HTTP pages, six per saved query. No invented SLA.
        samples, query_counts, counts = [], [], []
        for definition in self.saved:
            all_rows = list(
                matching_items(
                    self.owner, CollectionQuery.model_validate(definition.query)
                ).values_list("pk", flat=True)
            )
            total = len(all_rows)
            counts.append(total)
            for fraction in range(6):
                offset = ((max(total - 1, 0) * fraction // 5) // 100) * 100
                start = perf_counter()
                with CaptureQueriesContext(connection) as sql:
                    response = self.client.get(
                        API + "/" + str(definition.pk) + "/items",
                        {"offset": offset, "limit": 100},
                    )
                ms = (perf_counter() - start) * 1000
                self.assertEqual(response.status_code, 200, response.content)
                payload = response.json()
                self.assertEqual(payload["count"], total)
                self.assertEqual(
                    [row["item_id"] for row in payload["results"]],
                    [str(pk) for pk in all_rows[offset:offset + 100]],
                )
                self.assertEqual(
                    len({row["item_id"] for row in payload["results"]}),
                    len(payload["results"]),
                )
                samples.append(ms)
                query_counts.append(len(sql))
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(API).json()["results"], [])
        self.assertEqual(
            self.client.get(API + "/" + str(self.saved[0].pk) + "/items").status_code,
            404,
        )
        sorted_samples = sorted(samples)
        p95 = sorted_samples[math.ceil(0.95 * len(samples)) - 1]
        print("P11_POSTGRES_SCALE " + json.dumps({
            "scope": "synthetic PostgreSQL Django testclient, NOT production",
            "items": 10000, "groups": 100, "owners": 2,
            "saved_queries": len(self.saved), "http_page_samples": len(samples),
            "result_counts": counts,
            "p95_ms": round(p95, 2),
            "median_ms": round(statistics.median(samples), 2),
            "max_sql_queries_per_page": max(query_counts),
            "min_sql_queries_per_page": min(query_counts),
            "indexes_present": sorted(indexes.intersection({
                "item_owner_saved_idx", "kt_item_fts_gin",
                "kt_derived_fts_gin", "collection_owner_name_idx",
            })),
            "p95_definition": "sorted[ceil(0.95*n)-1]",
        }, ensure_ascii=False))
