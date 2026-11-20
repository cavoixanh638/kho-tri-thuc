from dataclasses import asdict, replace
from hashlib import sha256
from urllib.parse import urlsplit
from uuid import UUID

from catalog.models import Item, Source
from django.db import transaction
from django.db.models.functions import Now
from django.utils.dateparse import parse_datetime
from ingestion.models import CaptureEvent
from jobs.handlers import JobFailure
from jobs.models import Job
from jobs.repository import JobRepository

from .models import DerivedContent
from .source_cleaning import source_metadata, source_text
from .source_fetch import SourceResult, SourceStatus, fetch_source

WEB_TEXT = "web_text"
FAILED_STATUSES = {
    SourceStatus.NOT_FOUND,
    SourceStatus.ACCESS_DENIED,
    SourceStatus.BLOCKED,
    SourceStatus.FAILED,
}
RETRY_ERRORS = {"dns_error", "timeout", "network_error", "incomplete_body"}


def _scope(job):
    try:
        source_id = job.input_ref["source_id"]
        capture_id = UUID(job.input_ref["capture_id"])
        if type(source_id) is not int or source_id < 1:
            raise ValueError("Invalid source ID")
        source = Source.objects.select_related("item").get(
            pk=source_id, item_id=job.item_id
        )
        CaptureEvent.objects.only("pk").get(
            pk=capture_id,
            item_id=source.item_id,
            owner_id=source.item.owner_id,
            raw_kind=CaptureEvent.Kind.LINK,
        )
    except (
        Source.DoesNotExist,
        CaptureEvent.DoesNotExist,
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise JobFailure("invalid_source_job", retryable=False) from exc
    return source, capture_id


def _provenance(source, result):
    return {
        **asdict(result.provenance),
        "source_url": source.original_url,
        "requested_url": result.provenance.source_url,
        "attempted_at": result.provenance.attempted_at.isoformat(),
    }


def _current_text(source):
    return DerivedContent.objects.filter(
        item_id=source.item_id,
        asset__isnull=True,
        kind=WEB_TEXT,
        status=DerivedContent.Status.ACTIVE,
        source_locator__source_id=source.pk,
    )


def _store_text(source, current, result, provenance):
    cleaned = source_text(result.text)
    if not cleaned or not cleaned.strip():
        return False
    digest = sha256(cleaned.encode("utf-8")).hexdigest()
    processor = result.provenance.processor
    processor_version = result.provenance.processor_version
    if current.filter(
        input_hash=digest, processor=processor, processor_version=processor_version
    ).exists():
        return False

    old_ids = tuple(current.values_list("pk", flat=True))
    DerivedContent.objects.create(
        item_id=source.item_id,
        kind=WEB_TEXT,
        text=cleaned,
        source_locator={"source_id": source.pk, **provenance},
        processor=processor,
        processor_version=processor_version,
        input_hash=digest,
    )
    DerivedContent.objects.filter(pk__in=old_ids).update(
        status=DerivedContent.Status.STALE
    )
    return True


def _store_metadata(item, metadata, result):
    if result.metadata is None:
        return False
    changed = False
    for field, value in asdict(result.metadata).items():
        if isinstance(value, str):
            value = source_text(value)
        if not value:
            continue
        previous = metadata.get(field, "")
        if getattr(item, field) in {"", previous} and item.user_edit_version == 0:
            setattr(item, field, value)
        changed = changed or previous != value
        metadata[field] = value
    return changed


def _video_page(url):
    try:
        host = (urlsplit(url).hostname or "").lower().rstrip(".")
    except ValueError:
        return False
    domains = ("youtube.com", "youtu.be", "facebook.com", "fb.watch", "tiktok.com")
    return any(host == domain or host.endswith("." + domain) for domain in domains)


def _item_states(item, result, has_previous_text, video_page):
    has_text = bool(result.text and result.text.strip())
    if result.status in FAILED_STATUSES:
        item.source_fetch = "failed"
    else:
        item.source_fetch = "done" if has_text and not video_page else "partial"
    if has_text:
        item.content_extract = "partial" if video_page else "done"
    elif has_previous_text:
        item.content_extract = "partial"
    elif result.status == SourceStatus.FAILED:
        item.content_extract = "failed"
    else:
        item.content_extract = "not_available"
    if not item.assets.filter(role="original").exists():
        item.asset_storage = "not_applicable"
    media = item.assets.filter(role="original", mime="video/mp4").exclude(sha256="")
    if media.exists():
        item.source_fetch = "done"
        if media.filter(
            locations__status="verified", locations__provider="google_drive"
        ).exists():
            item.asset_storage = "verified"
    elif item.jobs.filter(kind="download_video").exists():
        downloading = item.jobs.filter(
            kind="download_video",
            state__in=[
                Job.State.QUEUED,
                Job.State.RUNNING,
                Job.State.RETRY,
            ],
        ).exists()
        item.source_fetch = "pending" if downloading else "failed"
        item.asset_storage = "pending" if downloading else "failed"


@transaction.atomic
def _persist(job, source, capture_id, result):
    if not (
        Job.objects.select_for_update()
        .filter(
            pk=job.pk,
            state=Job.State.RUNNING,
            lease_token=job.lease_token,
            lease_token__isnull=False,
            lease_until__gt=Now(),
        )
        .exists()
    ):
        return

    item = Item.objects.select_for_update().get(pk=source.item_id)
    source = Source.objects.select_for_update().get(pk=source.pk, item=item)
    metadata = source_metadata(dict(source.metadata))
    last_attempted_at = (
        metadata.get("fetch", {}).get("provenance", {}).get("attempted_at")
    )
    if (
        last_attempted_at
        and parse_datetime(last_attempted_at) > result.provenance.attempted_at
    ):
        return

    provenance = _provenance(source, result)
    current = _current_text(source)
    changed_text = _store_text(source, current, result, provenance)
    changed_metadata = _store_metadata(item, metadata, result)
    revision = metadata.get("evidence_revision", 0) + int(
        changed_text or changed_metadata
    )
    metadata["evidence_revision"] = revision
    metadata["fetch"] = {
        "status": result.status,
        "error_code": result.error_code,
        "available": list(result.available),
        "provenance": provenance,
    }
    source.metadata = metadata
    source.save(update_fields=["metadata"])

    _item_states(
        item,
        result,
        current.exists(),
        _video_page(source.original_url)
        or _video_page(result.provenance.response_url or ""),
    )
    item.save(
        update_fields=[
            "title",
            "description",
            "source_fetch",
            "content_extract",
            "asset_storage",
            "updated_at",
        ]
    )
    JobRepository.enqueue(
        kind="organize",
        idempotency_key=f"source:{source.pk}:evidence:{revision}",
        item=item,
        input_ref={
            "item_id": str(item.pk),
            "source_id": source.pk,
            "capture_id": str(capture_id),
        },
    )


def fetch_source_job(job: Job) -> None:
    from .video_jobs import enqueue_video

    source, capture_id = _scope(job)
    enqueue_video(job, source, capture_id)
    result: SourceResult = fetch_source(source.original_url.strip())
    result = replace(result, text=source_text(result.text))
    _persist(job, source, capture_id, result)
    if result.status in FAILED_STATUSES:
        status = result.provenance.http_status
        retryable = result.status == SourceStatus.FAILED and (
            result.error_code in RETRY_ERRORS
            or status in {408, 425, 429}
            or (status is not None and status >= 500)
        )
        raise JobFailure(
            result.error_code or "source_fetch_failed", retryable=retryable
        )
