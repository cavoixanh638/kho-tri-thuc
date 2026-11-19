import logging
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from googleapiclient.http import MediaIoBaseDownload
from storage.drive import DriveError
from storage.models import Asset, StorageLocation
from storage.oauth import client_for_owner
from storage.service import DRIVE_PROVIDER, DriveStorage

from .thumbnail import ThumbnailResult, ThumbnailService

logger = logging.getLogger(__name__)

_REBUILD_LIMIT = 32 * 1024 * 1024
_DOWNLOAD_CHUNK = 4 * 1024 * 1024
_MAX_CHUNKS = _REBUILD_LIMIT // _DOWNLOAD_CHUNK + 2


def thumbnail_service():
    cache_root = getattr(settings, "THUMBNAIL_CACHE_DIR", None)
    return (
        ThumbnailService(
            cache_root, ffmpeg=getattr(settings, "FFMPEG_BINARY", "ffmpeg")
        )
        if cache_root
        else None
    )


def verified_assets_for(owner_id):
    return Asset.objects.filter(
        item__owner_id=owner_id,
        item__deleted_at__isnull=True,
        locations__provider=DRIVE_PROVIDER,
        locations__status=StorageLocation.Status.VERIFIED,
    )


def _generate(service, asset, path):
    return service.generate(
        asset_id=asset.pk,
        content_sha256=asset.sha256,
        mime_type=asset.mime,
        source_path=path,
    )


def thumbnail_from_staging(asset, path):
    """Best-effort rendering while a verified upload's staged bytes are still present."""
    try:
        service = thumbnail_service()
        if service is not None and path.is_file():
            _generate(service, asset, path)
    except (OSError, RuntimeError, ValueError):
        # Upload verification is already durable. Only the preview is affected.
        logger.warning("thumbnail_generation_failed asset=%s", asset.pk)


class _SizedSink:
    def __init__(self, file, expected_size):
        self.file = file
        self.expected_size = expected_size
        self.size = 0

    def write(self, chunk):
        if self.size + len(chunk) > self.expected_size:
            raise DriveError("thumbnail_source_size_mismatch")
        written = self.file.write(chunk)
        self.size += written
        return written


def _download_verified_blob(client, file_id, expected_size, path):
    request = client.api.files().get_media(fileId=file_id)
    with path.open("wb") as file:
        sink = _SizedSink(file, expected_size)
        download = MediaIoBaseDownload(sink, request, chunksize=_DOWNLOAD_CHUNK)
        for _ in range(_MAX_CHUNKS):
            _, done = client.call(download.next_chunk)
            if done and sink.size == expected_size:
                return
            if done:
                break
    raise DriveError("thumbnail_source_size_mismatch")


def rebuild_thumbnail(asset_id, *, owner_id):
    """Restore a cache miss from an authenticated, bounded, hash-checked Drive download."""
    service = thumbnail_service()
    if service is None:
        return ThumbnailResult(None, None, "cache_disabled")

    asset = verified_assets_for(owner_id).get(pk=asset_id)
    cached = service.get_cached(asset.pk, asset.sha256)
    if cached is not None:
        return cached
    media_type = asset.mime.split(";", 1)[0].strip().lower()
    if media_type != "application/pdf" and not media_type.startswith(
        ("image/", "video/")
    ):
        return ThumbnailResult(None, None, "unsupported_media")
    if not asset.size or asset.size > _REBUILD_LIMIT:
        return ThumbnailResult(None, None, "thumbnail_source_size_unsupported")

    client, account = client_for_owner(owner_id)
    remote = DriveStorage(client, account).stat(asset)
    if (
        remote.size != asset.size
        or remote.mime != asset.mime
        or (remote.sha256 and remote.sha256.lower() != asset.sha256.lower())
    ):
        raise DriveError("thumbnail_source_changed")

    with TemporaryDirectory(prefix="kt-thumbnail-") as scratch:
        path = Path(scratch) / "source"
        _download_verified_blob(client, remote.file_id, asset.size, path)
        try:
            # ThumbnailService checks the full SHA-256 before decoding.
            return _generate(service, asset, path)
        except ValueError as exc:
            raise DriveError("thumbnail_source_checksum_mismatch") from exc
