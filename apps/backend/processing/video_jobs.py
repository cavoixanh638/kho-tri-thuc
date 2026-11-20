"""Fetch supported public videos, then hand durable staged bytes to Drive upload."""

import hashlib
import json
import math
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID, uuid5

from catalog.models import Item, Source
from django.conf import settings
from django.db import transaction
from django.db.models.functions import Now
from django.utils import timezone
from ingestion.models import CaptureEvent
from jobs.handlers import JobFailure
from jobs.models import Job
from jobs.repository import JobRepository
from storage.models import Asset, StorageLocation
from storage.upload_job import staging_path

from .source_cleaning import source_metadata, source_text

VIDEO_KIND = "download_video"
MAX_VIDEO_BYTES = 128 * 1024 * 1024


def _lease(job):
    return (
        Job.objects.select_for_update()
        .filter(
            pk=job.pk,
            item_id=job.item_id,
            state=Job.State.RUNNING,
            lease_token=job.lease_token,
            lease_token__isnull=False,
            lease_until__gt=Now(),
        )
        .exists()
    )


def _scope(job):
    try:
        source_id = job.input_ref["source_id"]
        capture_id = UUID(job.input_ref["capture_id"])
        if type(source_id) is not int or source_id < 1:
            raise ValueError
        source = Source.objects.select_related("item").get(
            pk=source_id,
            item_id=job.item_id,
            item__deleted_at__isnull=True,
        )
        CaptureEvent.objects.only("pk").get(
            pk=capture_id,
            owner_id=source.item.owner_id,
            item_id=source.item_id,
            raw_kind=CaptureEvent.Kind.LINK,
        )
    except (
        Source.DoesNotExist,
        CaptureEvent.DoesNotExist,
        KeyError,
        TypeError,
        ValueError,
        AttributeError,
    ) as error:
        raise JobFailure("invalid_video_job", retryable=False) from error
    return source, capture_id


@transaction.atomic
def enqueue_video(job, source, capture_id):
    """Create the independent download even when the HTML request later fails."""
    from .video_download import is_facebook_url

    if not is_facebook_url(source.original_url.strip()) or not _lease(job):
        return
    item = Item.objects.select_for_update().get(pk=source.item_id)
    queued = JobRepository.enqueue(
        kind=VIDEO_KIND,
        idempotency_key=f"source:{source.pk}:video:v1",
        item=item,
        input_ref={"source_id": source.pk, "capture_id": str(capture_id)},
    )
    if queued.state in {Job.State.QUEUED, Job.State.RUNNING, Job.State.RETRY}:
        Item.objects.filter(pk=item.pk).exclude(asset_storage="verified").update(
            source_fetch="pending",
            asset_storage="pending",
        )


def _fingerprint(path):
    digest = hashlib.sha256()
    count = 0
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            count += len(chunk)
            if count > MAX_VIDEO_BYTES:
                raise JobFailure("video_too_large", retryable=False)
            digest.update(chunk)
    if count == 0:
        raise JobFailure("video_empty", retryable=False)
    return count, digest.hexdigest()


def probe_video(path):
    """Probe local bytes only. Select one stream to keep machine output bounded."""
    binary = getattr(settings, "FFPROBE_BINARY", os.getenv("FFPROBE_BINARY", "ffprobe"))
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    results = []
    for selection, entries in (
        ("v:0", "stream=codec_type,width,height:format=format_name,duration"),
        ("a:0", "stream=codec_type"),
    ):
        try:
            run = subprocess.run(
                [
                    str(binary),
                    "-v",
                    "error",
                    "-protocol_whitelist",
                    "file",
                    "-format_whitelist",
                    "mov",
                    "-select_streams",
                    selection,
                    "-show_entries",
                    entries,
                    "-of",
                    "json",
                    str(path),
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=15,
                check=False,
                creationflags=flags,
                env={
                    key: os.environ[key]
                    for key in (
                        "PATH",
                        "SystemRoot",
                        "WINDIR",
                        "TEMP",
                        "TMP",
                        "TMPDIR",
                        "LANG",
                        "LC_ALL",
                    )
                    if key in os.environ
                },
            )
        except FileNotFoundError as error:
            raise JobFailure("video_probe_unavailable", retryable=False) from error
        except (OSError, subprocess.TimeoutExpired) as error:
            raise JobFailure("video_probe_failed", retryable=False) from error
        if run.returncode or len(run.stdout) > 64 * 1024:
            raise JobFailure("video_probe_failed", retryable=False)
        try:
            results.append(json.loads(run.stdout))
        except (ValueError, UnicodeError) as error:
            raise JobFailure("video_probe_failed", retryable=False) from error
    try:
        video = results[0]["streams"][0]
        audio = results[1]["streams"][0]
        media = results[0]["format"]
        duration = float(media["duration"])
        width, height = int(video["width"]), int(video["height"])
        valid = (
            video["codec_type"] == "video"
            and audio["codec_type"] == "audio"
            and "mp4" in media["format_name"].split(",")
            and math.isfinite(duration)
            and 0 < duration <= 86400
            and 0 < width <= 16384
            and 0 < height <= 16384
        )
    except (KeyError, IndexError, TypeError, ValueError, OverflowError) as error:
        raise JobFailure("video_invalid_media", retryable=False) from error
    if not valid:
        raise JobFailure("video_invalid_media", retryable=False)
    return {"duration": duration, "width": width, "height": height, "audio": True}


def _asset(source):
    value = source.metadata.get("video", {}).get("asset_id")
    if not value:
        return None
    try:
        return Asset.objects.get(
            pk=UUID(value), item_id=source.item_id, role="original", mime="video/mp4"
        )
    except (Asset.DoesNotExist, ValueError, TypeError, AttributeError) as error:
        raise JobFailure("video_asset_mismatch", retryable=False) from error


def _verified(asset):
    return asset.locations.filter(
        provider="google_drive",
        status=StorageLocation.Status.VERIFIED,
    ).exists()


@transaction.atomic
def _existing(job, source):
    if not _lease(job):
        return False, None
    source = Source.objects.select_for_update().get(pk=source.pk, item_id=job.item_id)
    asset = _asset(source)
    if asset and _verified(asset):
        Item.objects.filter(pk=source.item_id).update(
            source_fetch="done",
            asset_storage="verified",
        )
        return False, None
    return True, asset


def _upload_job(asset):
    job = JobRepository.enqueue(
        kind="upload_asset",
        idempotency_key=f"video-asset:{asset.pk}",
        item=asset.item,
        input_ref={"asset_id": str(asset.pk)},
    )
    if job.state in {Job.State.FAILED, Job.State.DONE} and not _verified(asset):
        Job.objects.filter(pk=job.pk).update(
            state=Job.State.RETRY,
            attempt=0,
            retry_at=timezone.now(),
            lease_token=None,
            lease_until=None,
            completed_at=None,
            error_code="",
        )


@transaction.atomic
def _persist(job, source, result, path, size, digest, media):
    if not _lease(job):
        return
    item = Item.objects.select_for_update().get(pk=source.item_id)
    source = Source.objects.select_for_update().get(pk=source.pk, item=item)
    asset = _asset(source)
    if asset is not None and (asset.size != size or asset.sha256 != digest):
        raise JobFailure("video_source_changed", retryable=False)
    if asset is None:
        asset, _ = Asset.objects.get_or_create(
            pk=uuid5(item.pk, f"facebook-source:{source.pk}"),
            defaults={
                "item": item,
                "mime": "video/mp4",
                "size": size,
                "sha256": digest,
                "original_filename": f"facebook-{source.pk}.mp4",
            },
        )
        if (asset.item_id, asset.mime, asset.size, asset.sha256) != (
            item.pk,
            "video/mp4",
            size,
            digest,
        ):
            raise JobFailure("video_asset_mismatch", retryable=False)
    target = staging_path(asset.pk)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not _verified(asset):
        if target.exists():
            if _fingerprint(target) != (size, digest):
                raise JobFailure("video_stage_changed", retryable=False)
        else:
            # File publication is atomic; the bounded private scratch is on this volume.
            with path.open("r+b") as stream:
                os.fsync(stream.fileno())
            os.replace(path, target)
            if hasattr(os, "O_DIRECTORY"):
                folder = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(folder)
                finally:
                    os.close(folder)
        _upload_job(asset)
    metadata = source_metadata(dict(source.metadata))
    metadata["video"] = {
        "status": "downloaded",
        "asset_id": str(asset.pk),
        "processor": "yt-dlp",
        "processor_version": "2026.10.26",
        "platform_id": str(result.platform_id)[:255],
        "downloaded_at": timezone.now().isoformat(),
        **media,
    }
    source.metadata = metadata
    source.platform = "facebook"
    source.platform_id = str(result.platform_id)[:255]
    source.save(update_fields=["metadata", "platform", "platform_id"])
    if item.user_edit_version == 0:
        # Existing fetched/curated metadata remains authoritative.
        if not item.title:
            item.title = source_text(str(result.title))[:512]
        if not item.description:
            item.description = source_text(str(result.description))[:20000]
    item.source_fetch = "done"
    item.asset_storage = "verified" if _verified(asset) else "pending"
    if item.content_extract == "pending":
        item.content_extract = "not_available"
    item.save(
        update_fields=[
            "title",
            "description",
            "source_fetch",
            "asset_storage",
            "content_extract",
            "updated_at",
        ]
    )


@transaction.atomic
def _failure(job, source, code):
    if not _lease(job):
        return
    source = Source.objects.select_for_update().get(pk=source.pk, item_id=job.item_id)
    metadata = dict(source.metadata)
    metadata["video"] = {
        **metadata.get("video", {}),
        "status": "failed",
        "error_code": code,
    }
    source.metadata = metadata
    source.save(update_fields=["metadata"])
    Item.objects.filter(pk=source.item_id).exclude(asset_storage="verified").update(
        source_fetch="failed",
        asset_storage="failed",
    )


def download_video(job):
    from .video_download import VideoDownloadError, download_facebook, is_facebook_url

    source, _capture_id = _scope(job)
    if not is_facebook_url(source.original_url.strip()):
        raise JobFailure("video_source_unsupported", retryable=False)
    proceed, asset = _existing(job, source)
    if not proceed:
        return
    try:
        if asset and staging_path(asset.pk).is_file():
            path = staging_path(asset.pk)
            size, digest = _fingerprint(path)
            if (size, digest) != (asset.size, asset.sha256):
                raise JobFailure("video_stage_changed", retryable=False)
            media = probe_video(path)
            from types import SimpleNamespace

            result = SimpleNamespace(
                platform_id=source.platform_id, title="", description=""
            )
            _persist(job, source, result, path, size, digest, media)
            return
        root = Path(settings.UPLOAD_STAGING_ROOT)
        root.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix="kt-video-", dir=root) as scratch:
            path = Path(scratch) / "original.mp4"
            result = download_facebook(source.original_url.strip(), path)
            if (
                Path(result.path).resolve() != path.resolve()
                or not path.is_file()
                or path.is_symlink()
            ):
                raise JobFailure("video_output_invalid", retryable=False)
            size, digest = _fingerprint(path)
            media = probe_video(path)
            _persist(job, source, result, path, size, digest, media)
    except VideoDownloadError as error:
        _failure(job, source, error.code)
        raise JobFailure(error.code, retryable=error.retryable) from None
    except JobFailure as error:
        _failure(job, source, error.code)
        raise
    except OSError as error:
        _failure(job, source, "video_stage_unavailable")
        raise JobFailure("video_stage_unavailable") from error
