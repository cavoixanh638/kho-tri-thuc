"""Shared, synthetic 30-send corpus: real PostgreSQL Events, no network/worker."""

import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from storage.models import Asset

from .models import CaptureEvent


@override_settings(ROOT_URLCONF="ingestion.test_capture")
class QuickCaptureCorpusTests(TestCase):
    def test_thirty_raw_receipts_retry_and_deliberate_resend(self):
        owner = get_user_model().objects.create_user(username="kt117-corpus")
        self.client.force_login(owner)
        corpus_path = Path(__file__).resolve().parent / "fixtures/kt117-fixtures.json"
        fixtures = json.loads(corpus_path.read_text(encoding="utf-8"))
        self.assertEqual(len(fixtures), 30)
        for index, fixture in enumerate(fixtures):
            with self.subTest(fixture=fixture["name"]):
                body = {
                    "kind": fixture["kind"],
                    "source_channel": "share",
                    "text": fixture["raw"],
                }
                if fixture["kind"] == "link":
                    body["url"] = fixture["url"]

                def post(key, data=body):
                    return self.client.post(
                        "/api/v1/captures",
                        json.dumps(data),
                        content_type="application/json",
                        headers={"Idempotency-Key": key},
                    )

                key = f"kt117-{index}"
                first = post(key)
                self.assertEqual(first.status_code, 201, first.content)
                event = CaptureEvent.objects.get(pk=first.json()["capture_id"])
                self.assertEqual(event.raw_kind, fixture["kind"])
                self.assertEqual(event.raw_text, fixture["raw"])
                self.assertEqual(event.original_url, fixture["url"])
                self.assertEqual(event.source_channel, "share")
                self.assertEqual(first.json()["item_id"], str(event.item_id))
                self.assertEqual(first.json()["state"], "received")
                self.assertTrue(first.json()["received_at"])
                self.assertEqual(CaptureEvent.objects.count(), index * 2 + 1)
                retry = post(key)
                self.assertEqual(retry.status_code, 200)
                self.assertEqual(retry.json(), first.json())
                self.assertEqual(CaptureEvent.objects.count(), index * 2 + 1)
                resend = post(key + "-new-send")
                self.assertEqual(resend.status_code, 201)
                self.assertNotEqual(resend.json()["capture_id"], str(event.pk))
                self.assertEqual(CaptureEvent.objects.count(), index * 2 + 2)
        self.assertEqual(CaptureEvent.objects.count(), 60)
        self.assertFalse(Asset.objects.exists(), "ACK is not a claim of saved media")
