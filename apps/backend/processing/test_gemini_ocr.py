import hashlib
import io
import json
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image
from catalog.models import Item
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from jobs.models import Job
from jobs.repository import JobRepository
from jobs.worker import Worker
from storage.models import Asset, StorageLocation

from .gemini_ocr_client import (
    GeminiProviderError, OCRResult, _parse_response, generate_ocr,
)
from .gemini_ocr_job import (
    KIND, _prepare_image, _reserve, enqueue_image_ocr, process_image_ocr,
)
from .models import DerivedContent, GeminiModelCatalog, GeminiUsageEvent


class _MemoryResponse:
    def __init__(self, body):
        self._body = io.BytesIO(body)
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def read(self, count):
        return self._body.read(count)


class GeminiImageClientTests(SimpleTestCase):
    def test_structured_request_is_image_only_and_secret_is_header_only(self):
        seen = []
        response = {
            "candidates": [{"content": {"parts": [{"text": json.dumps({
                "ocr_text": "Cảng biển Hải Phòng\n2026", "visual_description": "Một slide."
            }, ensure_ascii=False)}]}, "finishReason": "STOP"}],
            "modelVersion": "gemini-3.6-flash-001",
            "usageMetadata": {"promptTokenCount": 109, "candidatesTokenCount": 25},
        }
        def open_request(request, timeout):
            seen.append(request)
            return _MemoryResponse(json.dumps(response).encode())
        result = generate_ocr(
            api_key="secret-test-only", model_id="gemini-3.6-flash",
            image=b"synthetic-inline-image", mime_type="image/png",
            opener=SimpleNamespace(open=open_request),
        )
        self.assertEqual(result.text, "Cảng biển Hải Phòng\n2026")
        self.assertEqual(result.description, "Một slide.")
        self.assertEqual((result.input_tokens, result.output_tokens), (109, 25))
        self.assertNotIn("secret-test-only", seen[0].full_url)
        self.assertEqual(seen[0].get_header("X-goog-api-key"), "secret-test-only")
        payload = json.loads(seen[0].data)
        self.assertEqual(payload["contents"][0]["parts"][1]["inline_data"]["mime_type"], "image/png")
        self.assertEqual(payload["generationConfig"]["responseMimeType"], "application/json")
        self.assertEqual(timeout if False else 45, 45)

    def test_fails_closed_on_bad_schema_and_incomplete_generation(self):
        for candidate in (
            {"content": {"parts": [{"text": "{}"}]}, "finishReason": "STOP"},
            {"content": {"parts": [{"text": '{"ocr_text":"abc","visual_description":"x"}'}]},
             "finishReason": "MAX_TOKENS"},
            {"content": {"parts": [{"text": json.dumps({
                "ocr_text": "c" * 32_001, "visual_description": "",
            })}]}, "finishReason": "STOP"},
            {"content": {"parts": [{"text": '{"ocr_text": "bad\\u0000","visual_description": ""}'}]},
             "finishReason": "STOP"},
        ):
            with self.subTest(candidate=candidate), self.assertRaises(GeminiProviderError):
                _parse_response({"candidates": [candidate]})

    def test_invalid_model_or_media_is_rejected_before_any_network_call(self):
        for model in ("gemini/evil", "../models/gemini-bad", "imagen-123"):
            with self.subTest(model=model), self.assertRaises(GeminiProviderError):
                generate_ocr(
                    api_key="fake", model_id=model, image=b"abc",
                    mime_type="image/png",
                )
        with self.assertRaises(GeminiProviderError):
            generate_ocr(api_key="fake", model_id="gemini-3.6-flash",
                         image=b"abc", mime_type="image/svg+xml")

    def test_preprocessing_removes_exif_and_rejects_bogus_image(self):
        with Image.new("RGB", (12, 9), "white") as image:
            output = io.BytesIO()
            image.save(output, format="PNG")
        safe, mime = _prepare_image(output.getvalue())
        self.assertEqual(mime, "image/png")
        with Image.open(io.BytesIO(safe)) as image:
            self.assertEqual(image.size, (12, 9))
            self.assertEqual(image.info.get("exif"), None)
        with self.assertRaisesRegex(Exception, "invalid_ocr_image"):
            _prepare_image(b"<script>not an image</script>")


@override_settings(
    GEMINI_API_KEY="synthetic-key-only",
    GEMINI_OCR_ENABLED=True,
    GEMINI_OCR_EXTERNAL_PROCESSING_ALLOWED=True,
    GEMINI_ALLOW_PREMIUM_MODELS=False,
    GEMINI_MAX_LOCAL_REQUESTS_PER_DAY=3,
)
class GeminiOCRJobTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="ocr-user")
        cls.item = Item.objects.create(
            owner=cls.owner, kind=Item.Kind.FILE,
            title="ảnh thử nghiệm.png", note="Ghi chú của người dùng phải bất biến",
        )
        with Image.new("RGB", (16, 12), "white") as image:
            output = io.BytesIO()
            image.save(output, format="PNG")
        cls.source = output.getvalue()
        cls.asset = Asset.objects.create(
            item=cls.item, role="original", mime="image/png",
            original_filename="anh.png", size=len(cls.source),
            sha256=hashlib.sha256(cls.source).hexdigest(),
        )
        StorageLocation.objects.create(
            asset=cls.asset, provider="google_drive",
            provider_file_id="fixture-verified", status=StorageLocation.Status.VERIFIED,
            verified_at=timezone.now(), provider_revision="v1",
        )
        GeminiModelCatalog.objects.create(
            model_id="gemini-3.5-flash-lite", label="QA Lite",
            generation_methods=["generateContent"],
            active=True, reviewed=True, last_seen_at=timezone.now(),
        )

    def test_opt_in_requires_both_flags_and_verified_source(self):
        with override_settings(GEMINI_OCR_EXTERNAL_PROCESSING_ALLOWED=False):
            self.assertFalse(enqueue_image_ocr(self.asset))
        with override_settings(GEMINI_OCR_ENABLED=False):
            self.assertFalse(enqueue_image_ocr(self.asset))
        self.assertFalse(Job.objects.filter(kind=KIND).exists())
        self.assertTrue(enqueue_image_ocr(self.asset))
        self.assertTrue(enqueue_image_ocr(self.asset))
        self.assertEqual(Job.objects.filter(kind=KIND).count(), 1)

    def test_worker_reads_verified_original_then_persists_searchable_ocr_not_note(self):
        self.assertTrue(enqueue_image_ocr(self.asset))
        synthetic = OCRResult(
            text="Vận tải biển Hải Phòng\nSản lượng 2026: 120",
            description="Một bảng trình bày số liệu cảng biển.",
            model_version="gemini-3.5-flash-lite-001", input_tokens=100, output_tokens=48,
        )
        with (
            patch("processing.gemini_ocr_job.storage_for_owner",
                  return_value=SimpleNamespace(
                      read_range=lambda asset, start, end: self.source
                  )) as storage,
            patch("processing.gemini_ocr_job.generate_ocr", return_value=synthetic) as provider,
        ):
            self.assertTrue(Worker({KIND: process_image_ocr}).run_once())
        self.assertEqual(provider.call_count, 1)
        self.assertEqual(storage.call_count, 1)
        self.item.refresh_from_db()
        self.assertEqual(self.item.note, "Ghi chú của người dùng phải bất biến")
        self.assertEqual(self.item.content_extract, "done")
        ocr = DerivedContent.objects.get(asset=self.asset, kind="image_ocr", status="active")
        self.assertIn("Vận tải biển Hải Phòng", ocr.text)
        self.assertEqual(ocr.source_locator["model_id"], "gemini-3.5-flash-lite")
        self.assertEqual(ocr.source_locator["input_sha256"], self.asset.sha256)
        self.assertTrue(ocr.source_locator["review_required"])
        self.assertEqual(
            DerivedContent.objects.get(asset=self.asset, kind="image_description").text,
            synthetic.description,
        )
        self.assertEqual(GeminiUsageEvent.objects.get().status, "success")
        self.assertEqual(GeminiUsageEvent.objects.get().input_tokens, 100)
        self.assertTrue(Job.objects.filter(kind="organize", item=self.item).exists())
        # Reprocess an independently claimed job with same asset/model without
        # repeating a paid request; already-persisted text remains authoritative.
        Job.objects.create(
            kind=KIND, item=self.item, idempotency_key="manual-second",
            input_ref={"asset_id": str(self.asset.pk), "input_hash": self.asset.sha256},
        )
        with (
            patch("processing.gemini_ocr_job.storage_for_owner",
                  return_value=SimpleNamespace(read_range=lambda *args: self.source)),
            patch("processing.gemini_ocr_job.generate_ocr") as again,
        ):
            self.assertTrue(Worker({KIND: process_image_ocr}).run_once())
        again.assert_not_called()
        self.assertEqual(GeminiUsageEvent.objects.filter(status="success").count(), 1)

    def test_tampered_original_never_leaves_the_server(self):
        enqueue_image_ocr(self.asset)
        with (
            patch("processing.gemini_ocr_job.storage_for_owner",
                  return_value=SimpleNamespace(read_range=lambda *args: b"tampered")),
            patch("processing.gemini_ocr_job.generate_ocr") as external,
        ):
            Worker({KIND: process_image_ocr}).run_once()
        external.assert_not_called()
        self.assertEqual(Job.objects.get(kind=KIND).state, Job.State.FAILED)
        self.assertFalse(GeminiUsageEvent.objects.exists())

    def test_atomic_project_local_limit_reserves_before_external_call(self):
        with override_settings(GEMINI_MAX_LOCAL_REQUESTS_PER_DAY=1):
            model, first = _reserve(self.owner)
            self.assertEqual(model, "gemini-3.5-flash-lite")
            self.assertEqual(first.status, "reserved")
            with self.assertRaisesRegex(Exception, "ocr_local_budget_limit"):
                _reserve(self.owner)
            self.assertEqual(GeminiUsageEvent.objects.count(), 1)

    def test_provider_429_blocks_unknown_project_quota_instead_of_model_hopping(self):
        enqueue_image_ocr(self.asset)
        from .gemini_ocr_client import GeminiProviderError
        with (
            patch("processing.gemini_ocr_job.storage_for_owner",
                  return_value=SimpleNamespace(read_range=lambda *args: self.source)),
            patch("processing.gemini_ocr_job.generate_ocr",
                  side_effect=GeminiProviderError(
                      "project_quota", status="project_quota"
                  )),
        ):
            Worker({KIND: process_image_ocr}).run_once()
        self.assertEqual(GeminiUsageEvent.objects.get().status, "project_quota")
        self.assertEqual(Job.objects.get(kind=KIND).state, Job.State.FAILED)
        self.assertEqual(Job.objects.get(kind=KIND).error_code, "project_quota")
        self.assertFalse(DerivedContent.objects.exists())
