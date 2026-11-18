import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, connections, transaction
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from catalog.models import Item
from ingestion.models import CaptureEvent
from storage.drive import DriveError
from storage.models import Asset, StorageLocation
from storage.service import DriveStorage
from storage.test_drive_storage import FakeDrive

from .handlers import JobFailure
from .models import Job
from .repository import MAX_ATTEMPTS, RETRY_BASE_SECONDS, JobRepository
from .worker import Worker


class JobSchemaTests(TestCase):
    def test_idempotency_key_is_unique_per_job_kind(self):
        Job.objects.create(kind="fetch_source", idempotency_key="source:1")
        Job.objects.create(kind="organize", idempotency_key="source:1")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Job.objects.create(kind="fetch_source", idempotency_key="source:1")


class JobRepositoryTests(TestCase):
    def test_enqueue_keeps_the_first_payload_for_each_kind_and_key(self):
        first = JobRepository.enqueue(
            kind="fetch_source", idempotency_key="source:1", input_ref={"source_id": 1}
        )
        retry = JobRepository.enqueue(
            kind="fetch_source", idempotency_key="source:1", input_ref={"source_id": 2}
        )
        another_kind = JobRepository.enqueue(
            kind="organize", idempotency_key="source:1"
        )

        self.assertEqual(retry.pk, first.pk)
        self.assertEqual(retry.input_ref, {"source_id": 1})
        self.assertNotEqual(another_kind.pk, first.pk)
        self.assertEqual(Job.objects.count(), 2)

    def test_retry_is_delayed_and_stops_at_the_attempt_limit(self):
        job = JobRepository.enqueue(kind="organize", idempotency_key="item:1")

        def transient_failure(_job):
            raise JobFailure("drive_unavailable")

        worker = Worker({"organize": transient_failure})
        for attempt in range(1, MAX_ATTEMPTS + 1):
            started_at = timezone.now()
            self.assertTrue(worker.run_once())
            job.refresh_from_db()
            self.assertEqual(job.attempt, attempt)
            self.assertEqual(job.error_code, "drive_unavailable")
            self.assertIsNone(job.lease_token)
            self.assertIsNone(job.lease_until)
            if attempt < MAX_ATTEMPTS:
                self.assertEqual(job.state, Job.State.RETRY)
                self.assertGreaterEqual(
                    job.retry_at, started_at + timedelta(seconds=RETRY_BASE_SECONDS)
                )
                self.assertFalse(worker.run_once())
                Job.objects.filter(pk=job.pk).update(retry_at=started_at)

        self.assertEqual(job.state, Job.State.FAILED)
        self.assertIsNotNone(job.completed_at)
        self.assertFalse(worker.run_once())

    def test_permanent_failure_and_unknown_kinds(self):
        known = JobRepository.enqueue(kind="organize", idempotency_key="item:1")
        unknown = JobRepository.enqueue(kind="unknown", idempotency_key="item:2")

        def permanent_failure(_job):
            raise JobFailure("invalid_source", retryable=False)

        worker = Worker({"organize": permanent_failure})
        self.assertTrue(worker.run_once())
        self.assertFalse(worker.run_once())
        known.refresh_from_db()
        unknown.refresh_from_db()
        self.assertEqual(known.state, Job.State.FAILED)
        self.assertEqual(known.error_code, "invalid_source")
        self.assertEqual(known.attempt, 1)
        self.assertEqual(unknown.state, Job.State.QUEUED)
        self.assertEqual(unknown.attempt, 0)

    def test_expired_claim_cannot_finish_or_fail_a_reclaimed_job(self):
        job = JobRepository.enqueue(kind="organize", idempotency_key="item:1")
        first_claim = JobRepository.claim(["organize"])
        self.assertEqual(first_claim.pk, job.pk)
        self.assertIsNone(JobRepository.claim(["organize"]))
        Job.objects.filter(pk=job.pk).update(lease_until=timezone.now())
        self.assertFalse(JobRepository.complete(first_claim))
        second_claim = JobRepository.claim(["organize"])
        self.assertNotEqual(second_claim.lease_token, first_claim.lease_token)
        self.assertEqual(second_claim.attempt, 2)
        self.assertFalse(
            JobRepository.fail(first_claim, code="stale_worker", retryable=False)
        )
        self.assertTrue(JobRepository.complete(second_claim))
        job.refresh_from_db()
        self.assertEqual(job.state, Job.State.DONE)
        self.assertEqual(job.error_code, "")
        self.assertIsNotNone(job.completed_at)

    def test_crash_on_last_attempt_exhausts_the_job(self):
        job = JobRepository.enqueue(kind="organize", idempotency_key="item:1")
        Job.objects.filter(pk=job.pk).update(attempt=MAX_ATTEMPTS - 1)
        JobRepository.claim(["organize"])
        Job.objects.filter(pk=job.pk).update(lease_until=timezone.now())
        self.assertIsNone(JobRepository.claim(["organize"]))
        job.refresh_from_db()
        self.assertEqual(job.state, Job.State.FAILED)
        self.assertEqual(job.error_code, "lease_expired")
        self.assertIsNone(job.lease_token)
        self.assertIsNotNone(job.completed_at)


class DurableWorkerTests(TransactionTestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="worker-owner")

    def capture(self, *, kind="organize"):
        item = Item.objects.create(owner=self.owner, kind=Item.Kind.TEXT)
        event = CaptureEvent.objects.create(
            owner=self.owner,
            item=item,
            raw_kind=CaptureEvent.Kind.TEXT,
            raw_text="ghi chú thử worker",
        )
        job = JobRepository.enqueue(
            kind=kind,
            idempotency_key=f"capture:{event.pk}",
            item=item,
            input_ref={"capture_id": str(event.pk)},
        )
        return item, event, job

    def test_capture_item_and_job_roll_back_together(self):
        with transaction.atomic():
            self.capture()
            transaction.set_rollback(True)

        self.assertFalse(CaptureEvent.objects.exists())
        self.assertFalse(Item.objects.exists())
        self.assertFalse(Job.objects.exists())

    def test_claim_skips_a_job_locked_by_another_connection(self):
        locked_job = JobRepository.enqueue(kind="organize", idempotency_key="locked")
        other_job = JobRepository.enqueue(kind="organize", idempotency_key="free")

        def claim_on_another_connection():
            try:
                return JobRepository.claim(["organize"]).pk
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=1) as executor:
            with transaction.atomic():
                Job.objects.select_for_update().get(pk=locked_job.pk)
                claimed_id = executor.submit(claim_on_another_connection).result(
                    timeout=5
                )

        self.assertEqual(claimed_id, other_job.pk)
        self.assertEqual(JobRepository.claim(["organize"]).pk, locked_job.pk)

    def test_worker_recovers_after_process_exits_with_a_committed_claim(self):
        with transaction.atomic():
            item, event, job = self.capture()
        script = (
            "import os; from jobs.repository import JobRepository; "
            "JobRepository.claim(['organize']); os._exit(23)"
        )
        backend = Path(__file__).resolve().parents[1]
        crashed = subprocess.run(
            [sys.executable, "manage.py", "shell", "-c", script],
            cwd=backend,
            env={**os.environ, "POSTGRES_DB": connection.settings_dict["NAME"]},
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(crashed.returncode, 23, crashed.stderr)
        job.refresh_from_db()
        self.assertEqual(job.state, Job.State.RUNNING)
        self.assertEqual(job.attempt, 1)
        self.assertIsNotNone(job.lease_token)

        self.assertFalse(Worker({"organize": lambda _job: None}).run_once())
        Job.objects.filter(pk=job.pk).update(lease_until=timezone.now())
        handled = []

        def handle(recovered_job):
            self.assertFalse(connection.in_atomic_block)
            handled.append(recovered_job.pk)

        restarted = Worker({"organize": handle})
        self.assertTrue(restarted.run_once())
        self.assertFalse(restarted.run_once())
        job.refresh_from_db()
        self.assertEqual(handled, [job.pk])
        self.assertEqual(job.state, Job.State.DONE)
        self.assertEqual(job.attempt, 2)
        self.assertTrue(Item.objects.filter(pk=item.pk).exists())
        persisted_event = CaptureEvent.objects.get(pk=event.pk)
        self.assertEqual(persisted_event.raw_text, event.raw_text)
        self.assertEqual(persisted_event.server_received_at, event.server_received_at)

    def test_worker_retry_after_upload_response_loss_keeps_one_drive_asset(self):
        item, event, job = self.capture(kind="upload")
        payload = b"generated fixture"
        asset = Asset.objects.create(
            item=item,
            mime="text/plain",
            size=len(payload),
            sha256=sha256(payload).hexdigest(),
            original_filename="fixture.txt",
        )
        drive = FakeDrive()
        drive.lose_upload_response = True

        def upload(_job):
            storage = DriveStorage(
                drive, SimpleNamespace(owner_id=self.owner.pk, root_folder_id="root")
            )
            try:
                storage.save(asset, BytesIO(payload))
            except DriveError as error:
                raise JobFailure(error.code, retryable=error.retryable) from error

        self.assertTrue(Worker({"upload": upload}).run_once())
        job.refresh_from_db()
        self.assertEqual(job.state, Job.State.RETRY)
        Job.objects.filter(pk=job.pk).update(retry_at=timezone.now())
        self.assertTrue(Worker({"upload": upload}).run_once())
        job.refresh_from_db()

        self.assertEqual(job.state, Job.State.DONE)
        self.assertEqual(job.attempt, 2)
        self.assertEqual(drive.uploads, 1)
        self.assertEqual(drive.reservations, 1)
        self.assertEqual(asset.locations.get().status, StorageLocation.Status.VERIFIED)
        self.assertTrue(CaptureEvent.objects.filter(pk=event.pk, item=item).exists())
