from datetime import timedelta
from uuid import uuid4

from django.db import transaction
from django.db.models import Q
from django.db.models.functions import Now

from .models import Job

LEASE_DURATION = timedelta(minutes=10)
MAX_ATTEMPTS = 5
RETRY_BASE_SECONDS = 5
RETRY_CAP_SECONDS = 60


class JobRepository:
    @staticmethod
    def enqueue(*, kind, idempotency_key, item=None, input_ref=None) -> Job:
        """Preserve the first job for this kind/key, within the caller's transaction."""
        job, _created = Job.objects.get_or_create(
            kind=kind,
            idempotency_key=idempotency_key,
            defaults={
                "item": item,
                "input_ref": input_ref if input_ref is not None else {},
            },
        )
        return job

    @staticmethod
    @transaction.atomic
    def claim(kinds) -> Job | None:
        """Lock a single eligible job, releasing the lock before processing."""
        if not kinds:
            return None

        ready = Q(state__in=[Job.State.QUEUED, Job.State.RETRY], retry_at__lte=Now())
        expired = Q(state=Job.State.RUNNING) & (
            Q(lease_until__lte=Now()) | Q(lease_until__isnull=True)
        )
        job = (
            Job.objects.filter(ready | expired, kind__in=kinds)
            .select_for_update(skip_locked=True)
            .order_by("retry_at", "created_at", "pk")
            .first()
        )
        if job is None:
            return None

        if job.attempt >= MAX_ATTEMPTS:
            Job.objects.filter(pk=job.pk).update(
                state=Job.State.FAILED,
                lease_token=None,
                lease_until=None,
                completed_at=Now(),
                error_code="lease_expired",
            )
            return None

        job.state = Job.State.RUNNING
        job.attempt += 1
        job.lease_token = uuid4()
        job.lease_until = Now() + LEASE_DURATION
        job.save(update_fields=["state", "attempt", "lease_token", "lease_until"])
        job.refresh_from_db(fields=["lease_until"])
        return job

    @staticmethod
    def _active_lease(job):
        return Job.objects.filter(
            pk=job.pk,
            state=Job.State.RUNNING,
            lease_token=job.lease_token,
            lease_token__isnull=False,
            lease_until__gt=Now(),
        )

    @classmethod
    def complete(cls, job) -> bool:
        """A stale or expired claim cannot finish a job."""
        return bool(
            cls._active_lease(job).update(
                state=Job.State.DONE,
                lease_token=None,
                lease_until=None,
                completed_at=Now(),
                error_code="",
            )
        )

    @classmethod
    def fail(cls, job, *, code, retryable) -> bool:
        leased = cls._active_lease(job)
        if retryable and job.attempt < MAX_ATTEMPTS:
            delay = min(
                RETRY_BASE_SECONDS * (2 ** (job.attempt - 1)), RETRY_CAP_SECONDS
            )
            return bool(
                leased.update(
                    state=Job.State.RETRY,
                    retry_at=Now() + timedelta(seconds=delay),
                    lease_token=None,
                    lease_until=None,
                    error_code=code,
                )
            )
        return bool(
            leased.update(
                state=Job.State.FAILED,
                lease_token=None,
                lease_until=None,
                completed_at=Now(),
                error_code=code,
            )
        )
