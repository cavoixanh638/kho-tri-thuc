from catalog.models import Item, Source
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from storage.models import Asset, StorageLocation

from .models import DerivedContent
from .read_knowledge import ReadKnowledgeService


class LocatorProvenanceTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="locator-owner")
        self.other = get_user_model().objects.create_user(username="locator-other")
        self.item = Item.objects.create(owner=self.owner, kind="file")
        self.asset = Asset.objects.create(
            item=self.item,
            mime="application/pdf",
            sha256="a" * 64,
            original_filename="fixture.pdf",
            content_version=7,
        )
        StorageLocation.objects.create(
            asset=self.asset,
            provider_file_id="private-not-returned",
            status="verified",
            verified_at=timezone.now(),
        )
        self.part = DerivedContent.objects.create(
            item=self.item,
            asset=self.asset,
            kind="document_text",
            text="Fixture",
            processor="test",
            processor_version="v1",
            input_hash=self.asset.sha256,
            source_locator={"page": 4},
        )
        self.client.force_login(self.owner)

    def read(self):
        return self.client.get(f"/api/v1/items/{self.item.pk}/knowledge")

    def test_api_preserves_exact_asset_version_and_does_not_expose_storage_ids(self):
        response = self.read()
        self.assertEqual(response.status_code, 200)
        part = response.json()["parts"][0]
        self.assertEqual(part["asset_id"], str(self.asset.pk))
        self.assertEqual(
            part["source"],
            {
                "state": "current",
                "version": "a" * 64,
                "source_id": None,
                "source_url": None,
                "mime": "application/pdf",
                "asset_version": 7,
            },
        )
        self.assertNotIn("private-not-returned", response.content.decode())

    def test_changed_hash_missing_storage_and_unknown_hash_are_distinct(self):
        self.asset.sha256 = "b" * 64
        self.asset.save()
        self.assertEqual(self.read().json()["parts"][0]["source"]["state"], "stale")
        self.asset.sha256 = self.part.input_hash
        self.asset.save()
        self.asset.locations.update(status="inaccessible")
        self.assertEqual(self.read().json()["parts"][0]["source"]["state"], "missing")
        self.asset.locations.update(status="verified")
        self.asset.sha256 = ""
        self.asset.save()
        self.assertEqual(
            self.read().json()["parts"][0]["source"]["state"], "unverified"
        )

    def test_cross_item_and_cross_owner_asset_never_become_a_citation(self):
        for owner in (self.owner, self.other):
            foreign_item = Item.objects.create(owner=owner, kind="file")
            self.asset.item = foreign_item
            self.asset.save()
            part = self.read().json()["parts"][0]
            self.assertIsNone(part["asset_id"])
            self.assertEqual(part["source"]["state"], "missing")
            self.assertEqual(part["source"]["version"], "")
            self.assertIsNone(part["source"]["mime"])

    def test_multiple_assets_are_mapped_independently_and_stale_rows_stay_excluded(
        self,
    ):
        second = Asset.objects.create(
            item=self.item,
            mime="audio/wav",
            sha256="b" * 64,
            original_filename="fixture.wav",
        )
        StorageLocation.objects.create(
            asset=second,
            provider_file_id="private-2",
            status="verified",
            verified_at=timezone.now(),
        )
        row = DerivedContent.objects.create(
            item=self.item,
            asset=second,
            kind="document_text",
            text="Other fixture",
            processor="test",
            processor_version="v2",
            input_hash=second.sha256,
            source_locator={"start_ms": 1200},
        )
        parts = ReadKnowledgeService().read(self.item)["parts"]
        actual = {str(p["asset_id"]): p["source"]["version"] for p in parts}
        self.assertEqual(
            actual, {str(self.asset.pk): "a" * 64, str(second.pk): "b" * 64}
        )
        row.status = "stale"
        row.save()
        self.assertEqual(len(ReadKnowledgeService().read(self.item)["parts"]), 1)

    def test_web_source_id_must_belong_to_same_item_and_does_not_invent_anchor(self):
        self.part.asset = None
        source = Source.objects.create(
            item=self.item,
            original_url="https://example.invalid/article",
            canonical_url="https://example.invalid/article",
            identity_hash="c" * 64,
        )
        self.part.source_locator = {"source_id": source.pk, "section": "Heading"}
        self.part.save()
        evidence = self.read().json()["parts"][0]["source"]
        self.assertEqual(evidence["source_id"], source.pk)
        self.assertEqual(evidence["source_url"], source.original_url)
        foreign = Item.objects.create(owner=self.other, kind="link")
        source.item = foreign
        source.save()
        evidence = self.read().json()["parts"][0]["source"]
        self.assertEqual(evidence["state"], "missing")
        self.assertIsNone(evidence["source_url"])

    def test_api_owner_and_deleted_guards_apply_to_provenance(self):
        self.client.force_login(self.other)
        self.assertEqual(self.read().status_code, 404)
        self.client.force_login(self.owner)
        self.item.deleted_at = timezone.now()
        self.item.save()
        self.assertEqual(self.read().status_code, 404)

    def test_web_cached_text_does_not_claim_fresh_source_after_refetch_failure_or_change(
        self,
    ):
        source = Source.objects.create(
            item=self.item,
            original_url="https://example.invalid/web",
            canonical_url="https://example.invalid/web",
            identity_hash="d" * 64,
        )
        self.part.asset = None
        self.part.source_locator = {
            "source_id": source.pk,
            "source_url": source.original_url,
            "body_sha256": "body-v1",
        }
        self.part.save()
        for status, expected in [
            ("not_found", "missing"),
            ("access_denied", "missing"),
            ("failed", "unverified"),
        ]:
            source.metadata = {"fetch": {"status": status}}
            source.save()
            self.assertEqual(
                self.read().json()["parts"][0]["source"]["state"], expected
            )
        source.metadata = {
            "fetch": {"status": "fetched", "provenance": {"body_sha256": "body-v2"}}
        }
        source.save()
        self.assertEqual(self.read().json()["parts"][0]["source"]["state"], "stale")
