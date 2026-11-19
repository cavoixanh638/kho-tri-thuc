"""Durable, lease-fenced synchronization of a maximum of ten opted-in items."""

import hashlib
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from jobs.handlers import JobFailure
from jobs.models import Job
from jobs.repository import JobRepository
from storage.drive import DriveError
from storage.knowledge_export import DriveKnowledge
from storage.models import KnowledgeExport
from storage.oauth import client_for_owner

from .knowledge import snapshot

PILOT_LIMIT = 10


def _queue(record):
    if not Job.objects.filter(
        item_id=record.item_id,
        kind="export_knowledge",
        state__in=[Job.State.QUEUED, Job.State.RETRY],
    ).exists():
        JobRepository.enqueue(
            kind="export_knowledge",
            idempotency_key=f"knowledge:{record.item_id}:{uuid4()}",
            item=record.item,
            input_ref={"item_id": str(record.item_id)},
        )


@transaction.atomic
def request_sync(item_id, *, force=False):
    record = KnowledgeExport.objects.select_for_update().filter(item_id=item_id).first()
    if not record or (not record.enabled and record.status == "disabled" and not force):
        return
    current = snapshot(item_id, record.format)
    if (
        not force
        and record.status == "synced"
        and record.exported_version == current.version
    ):
        return
    record.source_version, record.status, record.last_error = (
        current.version,
        "pending",
        "",
    )
    record.save(update_fields=["source_version", "status", "last_error"])
    _queue(record)


@transaction.atomic
def configure(item, *, enabled, format):
    get_user_model().objects.select_for_update().get(pk=item.owner_id)
    record = KnowledgeExport.objects.select_for_update().filter(item=item).first()
    if (
        enabled
        and (not record or not record.enabled)
        and KnowledgeExport.objects.filter(
            item__owner_id=item.owner_id, enabled=True
        ).count()
        >= PILOT_LIMIT
    ):
        raise ValueError("knowledge_pilot_limit")
    record = record or KnowledgeExport(item=item)
    record.enabled, record.format = enabled, format
    record.status = "pending" if enabled or record.provider_file_id else "disabled"
    record.last_error = ""
    record.save()
    if record.status == "pending":
        transaction.on_commit(lambda: request_sync(item.pk, force=True))
    return record


def _locked_claim(job):
    active = JobRepository._active_lease(job).select_for_update().first()
    if not active:
        raise JobFailure("knowledge_lease_lost", retryable=False)


def export_knowledge(job):
    if not job.item_id:
        raise JobFailure("invalid_knowledge_job", retryable=False)
    try:
        # Persist a reserved identity before any external file creation. Later
        # retries (including process death after upload) always use this ID.
        with transaction.atomic():
            _locked_claim(job)
            record = (
                KnowledgeExport.objects.select_for_update(of=("self",))
                .select_related("item")
                .filter(item_id=job.item_id)
                .first()
            )
            if not record:
                return
            current = snapshot(job.item_id, record.format)
            active = record.enabled and bool(current.body) and not current.blocked
            if active and not record.provider_file_id:
                client, account = client_for_owner(record.item.owner_id)
                record.provider_file_id = DriveKnowledge(client, account).reserve()
                record.save(update_fields=["provider_file_id"])
        if active:
            # Folder ID must commit before external creation too. A network
            # failure in the upload transaction cannot roll this reservation back.
            client, account = client_for_owner(record.item.owner_id)
            DriveKnowledge(client, account).folder()
        # Serialize *network writes* as well as final state by the export row.
        # A new lease cannot write a later version before this holder exits.
        with transaction.atomic():
            _locked_claim(job)
            record = (
                KnowledgeExport.objects.select_for_update(of=("self",))
                .select_related("item")
                .get(item_id=job.item_id)
            )
            current = snapshot(job.item_id, record.format)
            active = record.enabled and bool(current.body) and not current.blocked
            if active and not record.provider_file_id:
                raise JobFailure("knowledge_state_changed")
            if record.provider_file_id:
                client, account = client_for_owner(record.item.owner_id)
                adapter = DriveKnowledge(client, account)
                if active:
                    adapter.save(record, current.body, current.version)
                else:
                    adapter.trash(record)
            _locked_claim(job)
            record.source_version = current.version
            record.truncated = current.truncated
            blocked = record.enabled and current.blocked
            record.last_error = "knowledge_sensitive_input" if blocked else ""
            record.status = "failed" if blocked else "synced" if active else "disabled"
            if active:
                record.exported_version = current.version
                record.content_sha256 = hashlib.sha256(current.body).hexdigest()
                record.last_synced_at = timezone.now()
            latest = snapshot(job.item_id, record.format)
            if latest.version != current.version:
                record.source_version, record.status = latest.version, "pending"
                _queue(record)
            record.save()
    except DriveError as error:
        with transaction.atomic():
            _locked_claim(job)
            record = KnowledgeExport.objects.select_for_update().get(
                item_id=job.item_id
            )
            record.status, record.last_error = "failed", error.code
            record.save(update_fields=["status", "last_error"])
        raise JobFailure(error.code, retryable=error.retryable) from None
