import json
from pathlib import Path
from uuid import UUID

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from jobs.models import Job
from processing.models import DerivedContent
from storage.models import Asset, StorageLocation

from .groups_api import _inline_item_links, _safe_locator
from .models import Item, ItemTopic, RelatedItem, Source, Topic

CORPUS = json.loads(
    (Path(__file__).parent / "fixtures/kt119-connections.json").read_text(
        encoding="utf-8"
    )
)


class RelatedConnectionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="kt119-owner")
        cls.other = get_user_model().objects.create_user(username="kt119-other")
        cls.items = {}
        for index, row in enumerate(CORPUS["items"]):
            cls.items[row["item_id"]] = Item.objects.create(
                id=UUID(row["item_id"]),
                owner=cls.owner,
                kind="text",
                title=row["title"],
                note=row["note"],
                user_edit_version=index,
            )
        cls.target = cls.items[CORPUS["target"]]
        topic = Topic.objects.create(owner=cls.owner, name="Nhóm đã cố định")
        ItemTopic.objects.create(item=cls.target, topic=topic, user_pinned=True)
        for row in CORPUS["items"]:
            peer = cls.items[row["item_id"]]
            if row["related"]:
                first, second = sorted([cls.target, peer], key=lambda item: item.pk)
                RelatedItem.objects.create(
                    item_a=first,
                    item_b=second,
                    relation_type=row["relation_type"],
                    reason=row["reason"],
                    confidence=row["confidence"],
                    method_version=row["method_version"],
                    source_version=row["source_version"],
                )
            if row["same_group"]:
                ItemTopic.objects.create(item=peer, topic=topic)

    def setUp(self):
        self.client.force_login(self.owner)
        self.url = f"/api/v1/items/{self.target.pk}/related"

    def test_thirty_items_have_fifteen_explicit_ten_related_five_group_counts(self):
        self.assertEqual(Item.objects.count(), 30)
        payload = self.client.get(self.url).json()
        self.assertEqual(payload["counts"], CORPUS["expected_counts"])
        for field, flag in [
            ("backlinks", "backlink"),
            ("results", "related"),
            ("same_group", "same_group"),
        ]:
            with self.subTest(field=field):
                expected = {row["item_id"] for row in CORPUS["items"] if row[flag]}
                actual = {row["item_id"] for row in payload[field]}
                self.assertEqual(actual, expected)
                self.assertEqual(len(payload[field]), len(expected))
                self.assertEqual(
                    Item.objects.filter(
                        pk__in=actual, owner=self.owner, deleted_at__isnull=True
                    ).count(),
                    len(expected),
                )
        self.assertEqual(payload["backlinks_scope"], "inline_markdown_only")
        self.assertEqual(
            len(
                {row["item_id"] for row in payload["backlinks"]}
                & {row["item_id"] for row in payload["results"]}
            ),
            1,
        )
        for row in payload["results"]:
            self.assertTrue(row["reason"])
            self.assertEqual(row["method_version"], "lexical-v3")
            self.assertTrue(row["source_version"].startswith("fixture-source-"))

    def test_parser_ignores_code_images_html_reference_links_and_invalid_destinations(
        self,
    ):
        destination = f"#/muc/{self.target.pk}"
        cases = [
            f"`[code]({destination})`",
            f"``[code]({destination})``",
            f"```markdown\n[fenced]({destination})\n```",
            f"~~~\n[fenced]({destination})\n~~~",
            f"    [indented]({destination})",
            f"\t[indented]({destination})",
            f"![image]({destination})",
            f"![image [nested]({destination})](x)",
            f"\\[escaped]({destination})",
            f"<div>\n[html]({destination})\n</div>",
            f"Text <script>[script]({destination})</script>",
            f"[reference][a]\n\n[a]: {destination}",
            destination,
            f"[external](https://evil.invalid/{destination})",
            f"[bad](<{destination})",
            f"[bad]({destination}>)",
            f"[suffix]({destination}-extra)",
            f"[masked]`code`({destination})",
            f"> ```\n> [quote-code]({destination})\n> ```",
            f"<!--\n\n[comment]({destination})\n-->",
            f"<script>\n\n[script]({destination})\n</script>",
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertEqual(_inline_item_links(text), set())
        self.assertEqual(
            _inline_item_links(f"[ok]({destination}) [again](<{destination}>)"),
            {self.target.pk},
        )
        self.assertEqual(
            _inline_item_links(f"`code` then [ok]({destination})"), {self.target.pk}
        )

    def test_owner_deleted_stale_and_unlinked_lexical_content_do_not_leak(self):
        foreign = Item.objects.create(
            owner=self.other,
            kind="text",
            title="PRIVATE FOREIGN",
            note=f"[actual](#/muc/{self.target.pk})",
        )
        deleted = Item.objects.create(
            owner=self.owner,
            kind="text",
            title="DELETED",
            note=f"[actual](#/muc/{self.target.pk})",
            deleted_at=timezone.now(),
        )
        misleading = Item.objects.create(
            owner=self.owner,
            kind="text",
            title="Only words",
            note=f"plain #/muc/{self.target.pk}",
        )
        for peer, status in [
            (foreign, "active"),
            (deleted, "active"),
            (misleading, "stale"),
        ]:
            first, second = sorted([self.target, peer], key=lambda item: item.pk)
            RelatedItem.objects.create(
                item_a=first,
                item_b=second,
                reason="Must not leak",
                method_version="test",
                source_version="test",
                status=status,
            )
        response = self.client.get(self.url)
        self.assertEqual(response.json()["counts"], CORPUS["expected_counts"])
        self.assertNotIn("PRIVATE FOREIGN", response.content.decode())
        self.assertNotIn("DELETED", response.content.decode())
        self.assertEqual(
            self.client.get(f"/api/v1/items/{foreign.pk}/related").status_code, 404
        )
        self.assertEqual(
            self.client.get(f"/api/v1/items/{deleted.pk}/related").status_code, 404
        )
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_read_only_endpoint_preserves_curated_groups_note_relations_and_jobs(self):
        before = {
            "items": list(Item.objects.order_by("id").values()),
            "groups": list(ItemTopic.objects.order_by("id").values()),
            "relations": list(RelatedItem.objects.order_by("id").values()),
            "jobs": Job.objects.count(),
        }
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(list(Item.objects.order_by("id").values()), before["items"])
        self.assertEqual(
            list(ItemTopic.objects.order_by("id").values()), before["groups"]
        )
        self.assertEqual(
            list(RelatedItem.objects.order_by("id").values()), before["relations"]
        )
        self.assertEqual(Job.objects.count(), before["jobs"])
        self.assertEqual(
            self.client.post(self.url, {}, content_type="application/json").status_code,
            405,
        )

    def test_source_and_asset_versions_use_actual_derived_associations(self):
        source = Source.objects.create(
            item=self.target,
            original_url="https://example.invalid/source",
            canonical_url="https://example.invalid/source",
            identity_hash="a" * 64,
        )
        unrelated_source = Source.objects.create(
            item=self.target,
            original_url="https://example.invalid/other",
            canonical_url="https://example.invalid/other",
            identity_hash="b" * 64,
        )
        assets = [
            Asset.objects.create(
                item=self.target,
                mime="application/pdf",
                original_filename=f"fixture-{index}.pdf",
                sha256=letter * 64,
                content_version=2,
            )
            for index, letter in enumerate("abc")
        ]
        StorageLocation.objects.create(
            asset=assets[0],
            status="verified",
            provider_file_id="fixture-file",
            verified_at=timezone.now(),
        )
        StorageLocation.objects.create(
            asset=assets[1], status="missing", provider_file_id="fixture-missing"
        )
        rows = []
        for index, asset in enumerate(assets[:2]):
            rows.append(
                DerivedContent.objects.create(
                    item=self.target,
                    asset=asset,
                    kind="document_text",
                    text="Văn bản hiện có",
                    source_locator={"source_id": source.pk, "page": index + 2},
                    processor="fixture-pdf",
                    processor_version="2",
                    input_hash=asset.sha256,
                )
            )
        old = DerivedContent.objects.create(
            item=self.target,
            asset=assets[0],
            kind="document_text",
            text="Bản cũ",
            source_locator={"source_id": source.pk, "page": 99},
            processor="fixture-pdf",
            processor_version="1",
            input_hash="0" * 64,
            status="stale",
        )
        mismatch = DerivedContent.objects.create(
            item=self.target,
            asset=assets[0],
            kind="document_text",
            text="Chưa xác minh hash",
            source_locator={"source_id": source.pk, "page": 88},
            processor="fixture-pdf",
            processor_version="1",
            input_hash="1" * 64,
        )
        web = DerivedContent.objects.create(
            item=self.target,
            kind="web_text",
            text="Văn bản web",
            source_locator={"source_id": unrelated_source.pk},
            processor="fixture-web",
            processor_version="1",
            input_hash="2" * 64,
        )
        payload = self.client.get(self.url).json()["evidence"]
        self.assertEqual(len(payload["sources"]), 2)
        self.assertEqual(len(payload["assets"]), 3)
        first = next(row for row in payload["sources"] if row["source_id"] == source.pk)
        self.assertEqual(
            set(first["asset_ids"]), {str(asset.pk) for asset in assets[:2]}
        )
        self.assertEqual(first["parts"], [])
        second = next(
            row for row in payload["sources"] if row["source_id"] == unrelated_source.pk
        )
        self.assertEqual([part["id"] for part in second["parts"]], [web.pk])
        by_id = {row["asset_id"]: row for row in payload["assets"]}
        self.assertEqual(
            [by_id[str(asset.pk)]["status"] for asset in assets],
            ["verified", "missing", "pending"],
        )
        self.assertEqual(by_id[str(assets[0].pk)]["content_version"], 2)
        parts = {part["id"]: part for row in payload["assets"] for part in row["parts"]}
        self.assertEqual(parts[rows[0].pk]["locator"], {"page": 2})
        self.assertTrue(parts[rows[0].pk]["matches_current_asset"])
        self.assertEqual(parts[old.pk]["locator"], {})
        self.assertEqual(parts[mismatch.pk]["locator"], {})
        self.assertFalse(parts[mismatch.pk]["matches_current_asset"])

    def test_foreign_source_asset_and_unsafe_locator_do_not_create_associations(self):
        foreign = Item.objects.create(
            owner=self.other, kind="file", title="PRIVATE FILE"
        )
        source = Source.objects.create(
            item=foreign,
            original_url="https://private.invalid",
            canonical_url="https://private.invalid",
            identity_hash="f" * 64,
        )
        asset = Asset.objects.create(
            item=foreign,
            mime="application/pdf",
            original_filename="PRIVATE_FILENAME.pdf",
            sha256="f" * 64,
        )
        part = DerivedContent.objects.create(
            item=self.target,
            asset=asset,
            kind="document_text",
            text="fixture",
            source_locator={
                "source_id": source.pk,
                "page": -1,
                "start_seconds": "Infinity",
                "url": "javascript:alert(1)",
            },
            processor="fixture",
            processor_version="1",
            input_hash="f" * 64,
        )
        payload = self.client.get(self.url).json()["evidence"]
        self.assertEqual(payload["sources"], [])
        self.assertEqual(payload["assets"], [])
        self.assertEqual(payload["unassociated_parts"][0]["id"], part.pk)
        self.assertIsNone(payload["unassociated_parts"][0]["asset_id"])
        self.assertIsNone(payload["unassociated_parts"][0]["source_id"])
        self.assertEqual(payload["unassociated_parts"][0]["locator"], {})
        self.assertNotIn("PRIVATE_FILENAME", json.dumps(payload))

    def test_empty_sample_has_zero_counts_without_an_accuracy_claim(self):
        empty = Item.objects.create(owner=self.owner, kind="text", title="Không có mẫu")
        data = self.client.get(f"/api/v1/items/{empty.pk}/related").json()
        self.assertEqual(
            data["counts"], {"related": 0, "backlinks": 0, "same_group": 0}
        )
        self.assertNotIn("accuracy", data)

    def test_lists_are_bounded_but_counts_are_not_silently_truncated(self):
        topic = Topic.objects.get(name="Nhóm đã cố định")
        for index in range(31):
            peer = Item.objects.create(
                owner=self.owner,
                kind="text",
                title=f"Extra {index}",
                note=f"[explicit](#/muc/{self.target.pk})",
            )
            first, second = sorted([self.target, peer], key=lambda item: item.pk)
            RelatedItem.objects.create(
                item_a=first,
                item_b=second,
                reason="Fixture only",
                method_version="fixture",
                source_version="fixture",
            )
            ItemTopic.objects.create(item=peer, topic=topic)
        data = self.client.get(self.url).json()
        self.assertEqual(
            data["counts"], {"backlinks": 46, "related": 41, "same_group": 36}
        )
        for key in ("backlinks", "results", "same_group"):
            self.assertEqual(len(data[key]), 30)

    def test_existing_asr_segments_normalize_only_finite_nonnegative_ordered_times(
        self,
    ):
        raw = {
            "segments": [
                {"start": 0, "end": 4, "text": "Một"},
                {"start": 4, "end": 9.5, "text": "Hai"},
            ]
        }
        self.assertEqual(
            _safe_locator(raw, True), {"start_seconds": 0, "end_seconds": 9.5}
        )
        self.assertEqual(_safe_locator(raw, False), {})
        for segments in [
            [],
            [{"start": -1, "end": 4}],
            [{"start": True, "end": 4}],
            [{"start": 0, "end": float("inf")}],
            [{"start": 4, "end": 5}, {"start": 2, "end": 3}],
            ["bad"],
        ]:
            with self.subTest(segments=segments):
                self.assertEqual(_safe_locator({"segments": segments}, True), {})
