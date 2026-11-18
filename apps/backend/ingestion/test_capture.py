import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Barrier
from unittest.mock import patch

from catalog.models import Item, Source
from django.contrib.auth import get_user_model
from django.db import DatabaseError, connections
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import path
from jobs.models import Job
from ninja import NinjaAPI
from storage.models import Asset

from .api import router
from .models import CaptureEvent
from .services import CaptureSubmission, submit_capture

test_api = NinjaAPI(urls_namespace="capture_test")
test_api.add_router("", router)
urlpatterns = [path("api/v1/", test_api.urls)]

CAPTURES = "/api/v1/captures"
FIRST_SERVER_TIME = datetime(2026, 11, 17, 1, 15, tzinfo=UTC)
SECOND_SERVER_TIME = datetime(2026, 11, 18, 4, 30, tzinfo=UTC)


@override_settings(ROOT_URLCONF=__name__)
class CaptureApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create(username="owner")
        cls.other = get_user_model().objects.create(username="other")

    def setUp(self):
        self.client.force_login(self.owner)

    def post(self, data, key=None):
        headers = {} if key is None else {"Idempotency-Key": key}
        return self.client.post(
            CAPTURES, json.dumps(data), content_type="application/json", headers=headers
        )

    def test_note_is_preserved_unicode_newlines_and_spaces_without_asset(self):
        raw_text = "  Tiếng Việt 👩🏽‍💻\r\n第二行\n \t"
        with patch("ingestion.services.timezone.now", return_value=FIRST_SERVER_TIME):
            response = self.post(
                {
                    "kind": "text",
                    "text": raw_text,
                    "client_sent_at": "2026-10-01T09:30:00+07:00",
                }
            )

        self.assertEqual(response.status_code, 201)
        event = CaptureEvent.objects.get(pk=response.json()["capture_id"])
        self.assertEqual(event.raw_text, raw_text)
        self.assertEqual(event.item.note, raw_text)
        self.assertEqual(event.item.saved_at, FIRST_SERVER_TIME)
        self.assertEqual(event.server_received_at, FIRST_SERVER_TIME)
        self.assertEqual(event.client_sent_at, datetime(2026, 10, 1, 2, 30, tzinfo=UTC))
        self.assertFalse(Asset.objects.exists())
        self.assertFalse(Source.objects.exists())
        job = Job.objects.get()
        self.assertEqual(job.kind, "organize")
        self.assertEqual(job.input_ref, {"capture_id": str(event.pk)})
        self.assertEqual(response.json()["state"], "received")

    def test_link_ack_records_original_and_queued_job_without_asset(self):
        original = " https://example.com/page?x=2#section "
        response = self.post({"kind": "link", "url": original})
        self.assertEqual(response.status_code, 201)
        event = CaptureEvent.objects.get(pk=response.json()["capture_id"])
        source = Source.objects.get(item=event.item)
        job = Job.objects.get(item=event.item)
        self.assertEqual(event.original_url, original)
        self.assertEqual(source.original_url, original)
        self.assertEqual(source.canonical_url, original.strip())
        self.assertEqual(event.item.saved_at, event.server_received_at)
        self.assertEqual(event.server_received_at, source.captured_at)
        self.assertEqual(job.kind, "fetch_source")
        self.assertEqual(job.state, Job.State.QUEUED)
        self.assertEqual(
            job.input_ref, {"capture_id": str(event.pk), "source_id": source.pk}
        )
        self.assertFalse(Asset.objects.exists())

    def test_retry_returns_same_receipt_even_after_processing_status_changes(self):
        data = {"kind": "link", "url": "https://example.com/404"}
        first = self.post(data, key="retry-request")
        self.assertEqual(first.status_code, 201)
        CaptureEvent.objects.update(status="processed")
        with patch("ingestion.services.timezone.now", return_value=SECOND_SERVER_TIME):
            retry = self.post(data, key="retry-request")
        self.assertEqual(retry.status_code, 200)
        self.assertEqual(retry.json(), first.json())
        self.assertEqual(CaptureEvent.objects.count(), 1)
        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(Job.objects.count(), 1)
        self.assertEqual(CaptureEvent.objects.get().original_url, data["url"])
        self.assertEqual(
            self.client.get(CAPTURES).json()["results"][0]["state"], "processed"
        )

    def test_link_resend_creates_new_event_preserves_annotations_and_curated_note(self):
        first_url = "https://youtu.be/dQw4w9WgXcQ?si=abc"
        second_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        first_annotation = "  Chú thích 1\n"
        second_annotation = "\nChú thích 2 "
        with patch("ingestion.services.timezone.now", return_value=FIRST_SERVER_TIME):
            first = self.post(
                {"kind": "link", "url": first_url, "text": first_annotation}
            )
        self.assertEqual(first.status_code, 201)
        item = Item.objects.get()
        item.note = "Ghi chú đã sửa"
        item.save(update_fields=["note"])
        with patch("ingestion.services.timezone.now", return_value=SECOND_SERVER_TIME):
            second = self.post(
                {"kind": "link", "url": second_url, "text": second_annotation}
            )
        self.assertEqual(second.status_code, 201)
        self.assertEqual(first.json()["item_id"], second.json()["item_id"])
        self.assertNotEqual(first.json()["capture_id"], second.json()["capture_id"])
        item.refresh_from_db()
        self.assertEqual(item.note, "Ghi chú đã sửa")
        self.assertEqual(item.saved_at, FIRST_SERVER_TIME)
        self.assertEqual(Source.objects.count(), 1)
        self.assertEqual(Job.objects.count(), 1)
        history = self.client.get(f"/api/v1/items/{item.pk}/captures").json()["results"]
        self.assertEqual(
            [entry["raw_text"] for entry in history],
            [second_annotation, first_annotation],
        )
        self.assertEqual(
            [entry["original_url"] for entry in history], [second_url, first_url]
        )
        self.assertEqual(
            CaptureEvent.objects.get(pk=second.json()["capture_id"]).server_received_at,
            SECOND_SERVER_TIME,
        )

    def test_distinct_notes_and_query_context_are_preserved(self):
        for _ in range(2):
            self.assertEqual(
                self.post({"kind": "text", "text": "Cùng câu chữ"}).status_code, 201
            )
        urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PL123",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=4",
            "https://example.com/?p=1",
            "https://example.com/?p=2",
            "https://example.com/?p=2#view",
        ]
        for url in urls:
            self.assertEqual(self.post({"kind": "link", "url": url}).status_code, 201)
        self.assertEqual(Item.objects.count(), 2 + len(urls))
        self.assertEqual(Source.objects.count(), len(urls))

    def test_unknown_aliases_and_local_addresses_are_rejected_without_enqueueing(self):
        local_urls = [
            "file:///private/path",
            "http://localhost",
            "http://www.localhost/",
            "http://127.1/",
            "http://0x7f.0.0.0x1/",
            "http://127.0.0.1/",
            "http://224.0.0.1/",
            "http://169.254.169.254/",
            "https://printer.local/",
            "http://[::1]/",
            "https://[2606:4700:4700::1111]example.com/",
            "https://[::ffff:127.0.0.1]/",
            "http://[fe80::1%25eth0]/",
            "https://login@public.example/",
            "https://public.example\\@localhost/",
        ]
        for url in local_urls:
            with self.subTest(url=url):
                self.assertEqual(
                    self.post({"kind": "link", "url": url}).status_code, 422
                )
        self.assertFalse(Job.objects.exists())
        self.assertFalse(Item.objects.exists())
        self.assertFalse(CaptureEvent.objects.exists())

    def test_empty_text_mixed_fields_and_invalid_request_keys_are_rejected(self):
        for payload, key in [
            ({"kind": "text", "text": "\n "}, None),
            ({"kind": "text", "text": "note", "url": "https://example.com"}, None),
            ({"kind": "text", "text": "note\x00"}, None),
            ({"kind": "text", "text": "note"}, "x" * 129),
            (
                {
                    "kind": "text",
                    "text": "note",
                    "client_sent_at": "2026-11-18T01:00:00",
                },
                None,
            ),
        ]:
            self.assertEqual(self.post(payload, key).status_code, 422)
        self.assertFalse(CaptureEvent.objects.exists())

    def test_history_date_filters_pagination_and_owner_scope(self):
        with patch("ingestion.services.timezone.now", return_value=FIRST_SERVER_TIME):
            older = self.post({"kind": "text", "text": "cũ"}, key="shared-key").json()
        with patch("ingestion.services.timezone.now", return_value=SECOND_SERVER_TIME):
            repeated = self.post({"kind": "text", "text": "mới"}, key="shared-key")
            self.assertEqual(repeated.json(), older)
            # A different channel may reuse a request key as a fresh submission.
            newer = self.post(
                {"kind": "text", "text": "mới", "source_channel": "android"},
                key="shared-key",
            ).json()

        self.client.force_login(self.other)
        other = self.post({"kind": "text", "text": "khác"}, key="shared-key").json()
        self.assertEqual(
            self.client.get(CAPTURES).json()["results"][0]["capture_id"],
            other["capture_id"],
        )
        self.assertEqual(
            self.client.get(f"/api/v1/items/{newer['item_id']}/captures").status_code,
            404,
        )
        self.client.force_login(self.owner)
        page = self.client.get(CAPTURES, {"limit": 1}).json()
        self.assertEqual(page["results"][0]["capture_id"], newer["capture_id"])
        self.assertEqual(page["next_offset"], 1)
        page = self.client.get(CAPTURES, {"limit": 1, "offset": 1}).json()
        self.assertEqual(page["results"][0]["capture_id"], older["capture_id"])
        self.assertIsNone(page["next_offset"])
        page = self.client.get(
            CAPTURES,
            {
                "received_from": FIRST_SERVER_TIME.isoformat(),
                "received_before": SECOND_SERVER_TIME.isoformat(),
            },
        ).json()
        self.assertEqual(
            [entry["capture_id"] for entry in page["results"]], [older["capture_id"]]
        )

    def test_authentication_and_csrf_required(self):
        self.client.logout()
        self.assertEqual(self.client.get(CAPTURES).status_code, 401)
        self.assertEqual(self.post({"kind": "text", "text": "n"}).status_code, 401)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(
            client.post(
                CAPTURES, '{"kind":"text","text":"n"}', content_type="application/json"
            ).status_code,
            403,
        )
        self.assertFalse(CaptureEvent.objects.exists())

    def test_failed_job_insert_rolls_back_event_item_and_source(self):
        with patch("ingestion.services.Job.objects.create", side_effect=DatabaseError):
            with self.assertRaises(DatabaseError):
                self.post({"kind": "link", "url": "https://example.com"})
        self.assertFalse(Item.objects.exists())
        self.assertFalse(Source.objects.exists())
        self.assertFalse(CaptureEvent.objects.exists())


class ConcurrentCaptureTests(TransactionTestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create(username="capture-race")

    def run_pair(self, key1, key2):
        barrier = Barrier(2)

        def submit(key):
            try:
                barrier.wait(timeout=10)
                event, created = submit_capture(
                    self.owner,
                    CaptureSubmission(
                        kind="link", url="https://example.com/page", idempotency_key=key
                    ),
                )
                return event.pk, event.item_id, created
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(submit, key) for key in (key1, key2)]
            return [future.result(timeout=20) for future in futures]

    def test_simultaneous_retry_shares_one_event_item_and_job(self):
        results = self.run_pair("key-1", "key-1")
        self.assertEqual(results[0][:2], results[1][:2])
        self.assertEqual({result[2] for result in results}, {True, False})
        self.assertEqual(CaptureEvent.objects.count(), 1)
        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(Source.objects.count(), 1)
        self.assertEqual(Job.objects.count(), 1)

    def test_simultaneous_true_submissions_create_distinct_events_with_one_item(self):
        results = self.run_pair("key-1", "key-2")
        self.assertNotEqual(results[0][0], results[1][0])
        self.assertEqual(results[0][1], results[1][1])
        self.assertTrue(all(result[2] for result in results))
        self.assertEqual(CaptureEvent.objects.count(), 2)
        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(Source.objects.count(), 1)
        self.assertEqual(Job.objects.count(), 1)
        self.assertEqual(
            Item.objects.get().saved_at,
            min(CaptureEvent.objects.values_list("server_received_at", flat=True)),
        )
