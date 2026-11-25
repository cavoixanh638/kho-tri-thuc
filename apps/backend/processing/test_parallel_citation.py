"""P06: authored notes and 30 independent PDF/ASR/web evidence scenarios."""

from catalog.models import Item, Source
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from storage.models import Asset, StorageLocation

from .models import DerivedContent
from .read_knowledge import ReadKnowledgeService


RAW_NOTE = "# Ghi chú biên soạn\nLời người viết <không thay đổi>.  \n"


class ParallelCitationTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="p06-owner")
        self.other = get_user_model().objects.create_user(username="p06-other")

    def make_case(self, modality, scenario, *, item=None):
        item = item or Item.objects.create(owner=self.owner, kind="link", note=RAW_NOTE)
        asset = None
        source = None
        if modality == "web":
            source = Source.objects.create(
                item=item,
                original_url="https://example.invalid/verified",
                canonical_url="https://example.invalid/verified",
                identity_hash="c" * 64,
                metadata={"fetch": {"status": "fetched", "provenance": {"body_sha256": "body-v1"}}},
            )
            locator = {
                "source_id": source.pk,
                "source_url": source.original_url,
                "body_sha256": "body-v1",
                "section": "Mục một",
            }
            kind, processor = "web_text", "public-web"
        else:
            mime = "application/pdf" if modality == "pdf" else "video/mp4"
            asset = Asset.objects.create(
                item=item,
                mime=mime,
                sha256="a" * 64,
                original_filename="fixture." + ("pdf" if modality == "pdf" else "mp4"),
                content_version=7,
            )
            StorageLocation.objects.create(
                asset=asset,
                provider_file_id="secret-drive-id-" + str(asset.pk),
                status="verified",
                verified_at=timezone.now(),
            )
            locator = {"page": 4} if modality == "pdf" else {"start_seconds": 2.5}
            kind, processor = ("document_text", "pdf-extract") if modality == "pdf" else ("video_transcript", "faster-whisper")
        part = DerivedContent.objects.create(
            item=item,
            asset=asset,
            kind=kind,
            text="Nội dung trích; không phải ghi chú.",
            processor=processor,
            processor_version="v1",
            input_hash="a" * 64,
            source_locator=locator,
        )

        if scenario == "no_locator":
            part.source_locator = {"source_id": source.pk} if source else {}
        elif scenario == "future_schema":
            part.source_locator = {**locator, "schema_version": 2}
        elif scenario == "stale_hash":
            if asset:
                asset.sha256 = "b" * 64
                asset.save()
            else:
                source.metadata = {"fetch": {"status": "fetched", "provenance": {"body_sha256": "body-v2"}}}
                source.save()
        elif scenario == "missing_origin":
            if asset:
                asset.locations.update(status="inaccessible")
            else:
                source.metadata = {"fetch": {"status": "not_found"}}
                source.save()
        elif scenario == "unverified":
            if asset:
                asset.sha256 = ""
                asset.save()
            else:
                source.metadata = {"fetch": {"status": "failed"}}
                source.save()
        elif scenario == "foreign_source":
            foreign = Item.objects.create(owner=self.other, kind="file")
            if asset:
                asset.item = foreign
                asset.save()
            else:
                source.item = foreign
                source.save()
        elif scenario == "new_version":
            part.processor_version = "v2"
            if asset:
                asset.content_version = 9
                asset.save()
            else:
                part.input_hash = "d" * 64
        elif scenario == "inactive_row":
            part.status = "stale"
        elif scenario == "bad_locator":
            if modality == "pdf":
                part.source_locator = {"page": "4"}
            elif modality == "asr":
                part.source_locator = {"start_seconds": -4}
            else:
                part.source_locator = {"source_id": source.pk, "section": ""}
        part.save()
        return item, part, asset, source

    def test_thirty_authored_citation_cases_preserve_separate_version_and_warning(self):
        scenarios = (
            "current", "no_locator", "future_schema", "stale_hash",
            "missing_origin", "unverified", "foreign_source", "new_version",
            "inactive_row", "bad_locator",
        )
        expected = (
            "current", "current", "current", "stale",
            "missing", "unverified", "missing", "current",
            None, "current",
        )
        count = 0
        for modality in ("pdf", "asr", "web"):
            for scenario, state in zip(scenarios, expected):
                with self.subTest(modality=modality, scenario=scenario):
                    item, part, asset, source = self.make_case(modality, scenario)
                    result = ReadKnowledgeService().read(item)
                    self.assertEqual(result["origin"], "authored")
                    self.assertEqual(result["text"], RAW_NOTE)
                    self.assertEqual(result["format"], "markdown")
                    self.assertFalse(result["needs_review"])
                    if state is None:
                        self.assertEqual(result["parts"], [])
                    else:
                        self.assertEqual(len(result["parts"]), 1)
                        citation = result["parts"][0]
                        self.assertEqual(citation["id"], part.pk)
                        self.assertEqual(citation["locator"], part.source_locator)
                        self.assertEqual(citation["source"]["state"], state)
                        self.assertEqual(citation["source"]["version"], part.input_hash if scenario != "foreign_source" or not asset else "")
                        self.assertEqual(citation["processor_version"], part.processor_version)
                        self.assertEqual(citation["source"]["asset_version"], asset.content_version if asset and scenario != "foreign_source" else None)
                        self.assertEqual(citation["source"]["source_id"], source.pk if source and scenario != "foreign_source" else None)
                        self.assertEqual(citation["asset_id"], asset.pk if asset and scenario != "foreign_source" else None)
                        if asset:
                            self.assertNotIn("secret-drive-id-" + str(asset.pk), str(citation))
                    count += 1
        self.assertEqual(count, 30)

    def test_authored_note_retains_pdf_asr_and_web_citations_without_transcript_priority(self):
        item = Item.objects.create(owner=self.owner, kind="link", note=RAW_NOTE)
        ids = {}
        for modality in ("pdf", "asr", "web"):
            _, part, _, _ = self.make_case(modality, "current", item=item)
            ids[modality] = part.pk
        self.client.force_login(self.owner)
        response = self.client.get(f"/api/v1/items/{item.pk}/knowledge")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["text"], RAW_NOTE)
        self.assertEqual(payload["origin"], "authored")
        self.assertEqual({row["id"] for row in payload["parts"]}, set(ids.values()))
        by_id = {row["id"]: row for row in payload["parts"]}
        self.assertEqual(by_id[ids["pdf"]]["locator"]["page"], 4)
        self.assertEqual(by_id[ids["asr"]]["locator"]["start_seconds"], 2.5)
        self.assertEqual(by_id[ids["web"]]["locator"]["section"], "Mục một")
        self.assertEqual(by_id[ids["web"]]["source"]["source_url"], "https://example.invalid/verified")
        item.refresh_from_db()
        self.assertEqual(item.note, RAW_NOTE)

    def test_orphan_extraction_does_not_fabricate_a_citation_for_authored_item(self):
        item = Item.objects.create(owner=self.owner, kind="text", note=RAW_NOTE)
        DerivedContent.objects.create(
            item=item, kind="web_text", text="Không có Source/Asset",
            processor="public-web", processor_version="v1", input_hash="a" * 64,
            source_locator={},
        )
        result = ReadKnowledgeService().read(item)
        self.assertEqual(result["text"], RAW_NOTE)
        self.assertEqual(result["parts"], [])

    def test_owner_deleted_and_unavailable_permissions_do_not_disclose_citations(self):
        item, _, asset, _ = self.make_case("pdf", "current")
        route = f"/api/v1/items/{item.pk}/knowledge"
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(route).status_code, 404)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(route).status_code, 200)
        asset.locations.update(status="inaccessible")
        self.assertEqual(self.client.get(route).json()["parts"][0]["source"]["state"], "missing")
        item.deleted_at = timezone.now()
        item.save()
        self.assertEqual(self.client.get(route).status_code, 404)
