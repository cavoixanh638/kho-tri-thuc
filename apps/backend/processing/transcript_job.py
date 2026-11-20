"""Download verified media to private scratch, transcribe offline, persist timed text."""

import hashlib
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic
from uuid import UUID

from django.conf import settings
from django.db import transaction
from googleapiclient.http import MediaIoBaseDownload
from jobs.handlers import JobFailure
from jobs.models import Job
from jobs.repository import JobRepository
from storage.drive import DriveError
from storage.models import Asset
from storage.service import storage_for_owner

from .models import DerivedContent
from .transcribe import (
    MAX_CHARS,
    MAX_SECONDS,
    MAX_SEGMENTS,
    PROCESSOR_VERSION,
    transcribe_file,
)


def _input_version(asset):
    return hashlib.sha256(f"{asset.sha256}:{PROCESSOR_VERSION}".encode()).hexdigest()


def enqueue_transcript(asset):
    if (
        not settings.LOCAL_ASR_MODEL_DIR
        or asset.role != "original"
        or asset.item.deleted_at
        or not asset.sha256
        or not asset.size
        or not asset.mime.startswith(("video/", "audio/"))
        or not asset.locations.filter(
            provider="google_drive", status="verified"
        ).exists()
    ):
        return False
    job = JobRepository.enqueue(
        kind="transcribe_media",
        idempotency_key=f"asr:{asset.pk}:{_input_version(asset)}",
        item=asset.item,
        input_ref={"asset_id": str(asset.pk)},
    )
    if job.state in {Job.State.QUEUED, Job.State.RETRY, Job.State.RUNNING}:
        type(asset.item).objects.filter(pk=asset.item_id).update(
            content_extract="pending"
        )
        return True
    return False


def _validate(result):
    if not isinstance(result, dict):
        raise JobFailure("invalid_transcript_result", retryable=False)
    if result.get("state") == "failed":
        code = result.get("error")
        raise JobFailure(
            code
            if code
            in {
                "transcript_model_missing",
                "transcript_duration_limit",
                "transcript_output_limit",
            }
            else "transcript_processing_failed",
            retryable=False,
        )
    if result.get("state") not in {"done", "not_available"}:
        raise JobFailure("invalid_transcript_result", retryable=False)
    rows = result.get("segments")
    if not isinstance(rows, list) or len(rows) > MAX_SEGMENTS:
        raise JobFailure("invalid_transcript_result", retryable=False)
    size, last_start = 0, 0
    for row in rows:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("text"), str)
            or not row["text"].strip()
            or "\x00" in row["text"]
        ):
            raise JobFailure("invalid_transcript_result", retryable=False)
        try:
            row["text"].encode()
        except UnicodeError as error:
            raise JobFailure("invalid_transcript_result", retryable=False) from error
        start, end = row.get("start"), row.get("end")
        if (
            not all(
                type(value) in {int, float} and math.isfinite(value)
                for value in (start, end)
            )
            or not last_start <= start <= end <= MAX_SECONDS + 1
        ):
            raise JobFailure("invalid_transcript_result", retryable=False)
        last_start = start
        size += len(row["text"])
    if (
        size > MAX_CHARS
        or (result["state"] == "done" and not rows)
        or (result["state"] == "not_available" and rows)
    ):
        raise JobFailure("invalid_transcript_result", retryable=False)
    if not isinstance(result.get("language", ""), str) or not isinstance(
        result.get("model_revision", ""), str
    ):
        raise JobFailure("invalid_transcript_result", retryable=False)
    return rows


def _timing(seconds):
    return f"{int(seconds) // 60:02d}:{int(seconds) % 60:02d}"


def _check_lease(job):
    if not JobRepository._active_lease(job).exists():
        raise JobFailure("transcript_lease_lost", retryable=False)


@transaction.atomic
def _status(job, *, empty=False):
    if not JobRepository._active_lease(job).select_for_update().exists():
        return
    from catalog.models import Item

    item = Item.objects.select_for_update().filter(pk=job.item_id).first()
    if not item or item.deleted_at:
        return
    usable = (
        bool(item.note.strip())
        or DerivedContent.objects.filter(item=item, status="active")
        .exclude(text="")
        .exists()
    )
    item.content_extract = (
        "partial" if usable else "not_available" if empty else "failed"
    )
    item.save(update_fields=["content_extract", "updated_at"])


def transcribe_media(job):
    try:
        _transcribe_media(job)
    except DriveError as error:
        _status(job)
        raise JobFailure(error.code, retryable=error.retryable) from None
    except JobFailure:
        _status(job)
        raise
    except (OSError, ValueError, TypeError, AttributeError) as error:
        _status(job)
        raise JobFailure("transcript_processing_failed", retryable=False) from error


def _transcribe_media(job):
    _check_lease(job)
    try:
        asset = Asset.objects.select_related("item").get(
            pk=UUID(job.input_ref["asset_id"]),
            item_id=job.item_id,
            role="original",
            item__deleted_at__isnull=True,
        )
    except (
        Asset.DoesNotExist,
        KeyError,
        ValueError,
        TypeError,
        AttributeError,
    ) as error:
        raise JobFailure("invalid_transcript_job", retryable=False) from error
    existing = DerivedContent.objects.filter(
        asset=asset,
        kind="video_transcript",
        input_hash=asset.sha256,
        processor_version=PROCESSOR_VERSION,
        status="active",
    )
    if existing.exists():
        with transaction.atomic():
            if not JobRepository._active_lease(job).select_for_update().exists():
                raise JobFailure("transcript_lease_lost", retryable=False)
            type(asset.item).objects.filter(
                pk=asset.item_id, deleted_at__isnull=True
            ).update(content_extract="done")
        return
    if (
        not asset.mime.startswith(("video/", "audio/"))
        or not asset.size
        or asset.size > 128 * 1024 * 1024
    ):
        raise JobFailure("transcript_media_size_limit", retryable=False)
    if not asset.locations.filter(provider="google_drive", status="verified").exists():
        raise JobFailure("transcript_media_not_verified", retryable=False)
    if not settings.LOCAL_ASR_MODEL_DIR:
        raise JobFailure("transcript_model_missing", retryable=False)
    storage = storage_for_owner(asset.item.owner_id)
    remote = storage.stat(asset)
    if (
        remote.sha256 != asset.sha256
        or remote.size != asset.size
        or remote.mime != asset.mime
    ):
        raise JobFailure("transcript_source_changed", retryable=False)
    scratch = Path(settings.THUMBNAIL_CACHE_DIR).parent / "transcript-scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="asr-", dir=scratch) as directory:
        path = Path(directory) / "source-media"
        with path.open("wb") as target:
            reader = MediaIoBaseDownload(
                target,
                storage.client.api.files().get_media(fileId=remote.file_id),
                chunksize=4 * 1024 * 1024,
            )
            done = False
            deadline = monotonic() + 120
            for _ in range(asset.size // (4 * 1024 * 1024) + 3):
                _check_lease(job)
                if monotonic() > deadline:
                    raise JobFailure("transcript_download_timeout")
                _, done = storage.client.call(reader.next_chunk)
                if target.tell() > asset.size:
                    raise JobFailure("transcript_source_changed", retryable=False)
                if done:
                    break
        with path.open("rb") as source:
            sha = hashlib.file_digest(source, "sha256").hexdigest()
        if not done or path.stat().st_size != asset.size or sha != asset.sha256:
            raise JobFailure("transcript_source_changed", retryable=False)
        _check_lease(job)
        result = transcribe_file(path, settings.LOCAL_ASR_MODEL_DIR)
    rows = _validate(result)
    with transaction.atomic():
        if not JobRepository._active_lease(job).select_for_update().exists():
            raise JobFailure("transcript_lease_lost", retryable=False)
        item = type(asset.item).objects.select_for_update().get(pk=asset.item_id)
        if item.deleted_at:
            return
        if not existing.exists():
            # One ordered transcript per asset avoids lexicographic UUID segment ordering.
            if rows:
                DerivedContent.objects.filter(
                    asset=asset, kind="video_transcript", status="active"
                ).update(status="stale")
                text = "\n\n".join(
                    f"[{_timing(row['start'])}–{_timing(row['end'])}] {row['text']}"
                    for row in rows
                )
                DerivedContent.objects.create(
                    item=item,
                    asset=asset,
                    kind="video_transcript",
                    text=text,
                    source_locator={
                        "section": "Bản chép lời có mốc thời gian",
                        "segments": rows,
                        "language": result.get("language", ""),
                        "model_revision": result.get("model_revision", ""),
                        "automatic": True,
                    },
                    processor="faster-whisper",
                    processor_version=PROCESSOR_VERSION,
                    input_hash=asset.sha256,
                )
            has_usable = (
                bool(item.note.strip())
                or DerivedContent.objects.filter(item=item, status="active")
                .exclude(text="")
                .exists()
            )
            item.content_extract = (
                "done" if rows else "partial" if has_usable else "not_available"
            )
            item.save(update_fields=["content_extract", "updated_at"])
            JobRepository.enqueue(
                kind="organize",
                idempotency_key=f"asr-organize:{asset.pk}:{_input_version(asset)}",
                item=item,
            )
