from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TransactionTestCase
from django.utils import timezone

from catalog.models import Item, Source
from ingestion.models import CaptureEvent
from jobs.models import Job
from jobs.repository import JobRepository
from jobs.worker import Worker

from .models import DerivedContent
from .source_fetch import SourceMetadata, SourceProvenance, SourceResult, SourceStatus
from .source_jobs import fetch_source_job

URL = "https://example.org/article"


class SourceJobTests(TransactionTestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="job-owner")
        self.item = Item.objects.create(owner=self.owner, kind=Item.Kind.LINK)
        self.capture = CaptureEvent.objects.create(
            owner=self.owner,
            item=self.item,
            raw_kind=CaptureEvent.Kind.LINK,
            original_url=f" {URL} ",
            raw_text="Ghi chú nguyên văn",
        )
        self.source = Source.objects.create(
            item=self.item,
            original_url=self.capture.original_url,
            canonical_url=URL,
            identity_hash="test-source",
        )
        self.worker = Worker({"fetch_source": fetch_source_job})

    def enqueue(self, key="first", **overrides):
        return JobRepository.enqueue(
            kind="fetch_source",
            idempotency_key=key,
            item=self.item,
            input_ref={
                "source_id": self.source.pk,
                "capture_id": str(self.capture.pk),
                **overrides,
            },
        )

    def result(
        self,
        status=SourceStatus.FETCHED,
        *,
        metadata=None,
        text=None,
        error=None,
        http_status=200,
        attempted_at=None,
    ):
        return SourceResult(
            status,
            SourceProvenance(
                URL,
                attempted_at or timezone.now(),
                response_url=URL,
                http_status=http_status,
                content_type="text/html",
                body_sha256="body-fixture",
            ),
            metadata=metadata,
            text=text,
            error_code=error,
        )

    def run_result(self, result):
        def fake_fetch(_url):
            self.assertFalse(connection.in_atomic_block)
            return result

        with patch(
            "processing.source_jobs.fetch_source", side_effect=fake_fetch
        ) as mocked:
            self.assertTrue(self.worker.run_once())
            mocked.assert_called_once_with(URL)

    def test_success_stores_provenance_and_preserves_immutable_capture(self):
        saved_at = self.item.saved_at
        job = self.enqueue()
        self.run_result(
            self.result(
                metadata=SourceMetadata("Một bài viết", "Giới thiệu"),
                text="Văn bản đã lấy",
            )
        )
        for model in (job, self.item, self.source):
            model.refresh_from_db()
        self.assertEqual(job.state, Job.State.DONE)
        self.assertEqual(self.item.source_fetch, "done")
        self.assertEqual(self.item.content_extract, "done")
        self.assertEqual(self.item.asset_storage, "not_applicable")
        self.assertEqual(self.item.title, "Một bài viết")
        self.assertEqual(
            self.source.metadata["fetch"]["available"], ["metadata", "web_text"]
        )
        self.assertEqual(
            self.source.metadata["fetch"]["provenance"]["source_url"], f" {URL} "
        )
        derived = DerivedContent.objects.get(item=self.item)
        self.assertEqual(derived.source_locator["source_id"], self.source.pk)
        self.assertEqual(derived.source_locator["body_sha256"], "body-fixture")
        self.assertEqual(derived.text, "Văn bản đã lấy")
        self.assertEqual(Job.objects.filter(kind="organize", item=self.item).count(), 1)
        self.assertEqual(self.item.saved_at, saved_at)
        capture = CaptureEvent.objects.get(pk=self.capture.pk)
        self.assertEqual(capture.server_received_at, self.capture.server_received_at)
        self.assertEqual(capture.original_url, self.capture.original_url)
        self.assertEqual(capture.raw_text, self.capture.raw_text)

    def test_retry_keeps_current_text_then_changes_version_once(self):
        initial = self.enqueue()
        self.run_result(self.result(text="Phiên bản đầu"))
        initial.refresh_from_db()
        first = DerivedContent.objects.get(item=self.item)
        retry = self.enqueue("refresh")
        self.run_result(
            self.result(SourceStatus.FAILED, error="timeout", http_status=None)
        )
        retry.refresh_from_db()
        first.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(retry.state, Job.State.RETRY)
        self.assertEqual(retry.error_code, "timeout")
        self.assertEqual(first.status, DerivedContent.Status.ACTIVE)
        self.assertEqual(self.item.source_fetch, "failed")
        self.assertEqual(self.item.content_extract, "partial")
        Job.objects.filter(pk=retry.pk).update(retry_at=timezone.now())
        self.run_result(self.result(text="Phiên bản mới"))
        self.enqueue("another-read")
        self.run_result(self.result(text="Phiên bản mới"))
        first.refresh_from_db()
        self.assertEqual(first.status, DerivedContent.Status.STALE)
        self.assertEqual(DerivedContent.objects.filter(item=self.item).count(), 2)
        self.assertEqual(
            DerivedContent.objects.get(status=DerivedContent.Status.ACTIVE).text,
            "Phiên bản mới",
        )
        self.assertEqual(Job.objects.filter(kind="organize").count(), 2)

    def test_video_page_evidence_is_partial_and_does_not_rewrite_user_edits(self):
        self.source.original_url = "https://www.youtube.com/watch?v=abcdefghijk"
        self.source.save(update_fields=["original_url"])
        self.item.title = "Tiêu đề đã sửa"
        self.item.description = ""
        self.item.user_edit_version = 2
        self.item.save(update_fields=["title", "description", "user_edit_version"])
        self.enqueue()
        with patch(
            "processing.source_jobs.fetch_source",
            return_value=self.result(
                metadata=SourceMetadata("External title", "External description"),
                text="Trang video, không phải phụ đề",
            ),
        ):
            self.assertTrue(self.worker.run_once())
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, "Tiêu đề đã sửa")
        self.assertEqual(self.item.description, "")
        self.assertEqual(self.item.source_fetch, "partial")
        self.assertEqual(self.item.content_extract, "partial")
        self.assertEqual(self.item.asset_storage, "not_applicable")
        self.assertEqual(DerivedContent.objects.get(item=self.item).kind, "web_text")

    def test_404_is_terminal_and_retains_original_evidence(self):
        job = self.enqueue()
        self.run_result(
            self.result(SourceStatus.NOT_FOUND, error="http_not_found", http_status=404)
        )
        job.refresh_from_db()
        self.source.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(job.state, Job.State.FAILED)
        self.assertEqual(self.item.source_fetch, "failed")
        self.assertEqual(self.item.content_extract, "not_available")
        self.assertEqual(
            self.source.metadata["fetch"]["provenance"]["http_status"], 404
        )
        self.assertFalse(DerivedContent.objects.exists())
        self.assertTrue(
            CaptureEvent.objects.filter(pk=self.capture.pk, item=self.item).exists()
        )

    def test_a_job_cannot_fetch_another_items_source(self):
        other_item = Item.objects.create(owner=self.owner, kind=Item.Kind.LINK)
        foreign = Source.objects.create(
            item=other_item,
            original_url=URL,
            canonical_url=URL,
            identity_hash="foreign",
        )
        job = self.enqueue(source_id=foreign.pk)
        with patch("processing.source_jobs.fetch_source") as mocked:
            self.assertTrue(self.worker.run_once())
            mocked.assert_not_called()
        job.refresh_from_db()
        self.assertEqual(job.error_code, "invalid_source_job")
        self.assertEqual(job.state, Job.State.FAILED)

    def test_stale_lease_cannot_persist_business_results(self):
        self.enqueue()
        expired = JobRepository.claim(["fetch_source"])
        Job.objects.filter(pk=expired.pk).update(
            lease_until=timezone.now() - timedelta(seconds=1)
        )
        current = JobRepository.claim(["fetch_source"])
        self.assertNotEqual(current.lease_token, expired.lease_token)
        with patch(
            "processing.source_jobs.fetch_source", return_value=self.result(text="Cũ")
        ):
            fetch_source_job(expired)
        self.source.refresh_from_db()
        self.assertEqual(self.source.metadata, {})
        self.assertFalse(DerivedContent.objects.exists())
        self.assertFalse(Job.objects.filter(kind="organize").exists())
