from pathlib import Path
from uuid import UUID

from django.conf import settings

from catalog.models import Item
from jobs.handlers import JobFailure
from processing.thumbnail_integration import thumbnail_from_staging

from .drive import DriveError
from .models import Asset, StorageLocation
from .service import DRIVE_PROVIDER, storage_for_owner

UPLOAD_KIND = "upload_asset"


def staging_path(asset_id: UUID) -> Path:
    return Path(settings.UPLOAD_STAGING_ROOT) / asset_id.hex


def _upload_asset(job):
    try:
        asset_id = UUID(job.input_ref["asset_id"])
        return Asset.objects.select_related("item").get(
            pk=asset_id, item_id=job.item_id
        )
    except (Asset.DoesNotExist, AttributeError, KeyError, TypeError, ValueError) as exc:
        raise JobFailure("invalid_upload_job", retryable=False) from exc


def _verified(asset):
    return asset.locations.filter(
        provider=DRIVE_PROVIDER, status=StorageLocation.Status.VERIFIED
    ).exists()


def upload_asset(job):
    asset = _upload_asset(job)
    path = staging_path(asset.pk)
    if not _verified(asset):
        try:
            file = path.open("rb")
        except FileNotFoundError as exc:
            if _verified(asset):
                return
            raise JobFailure("upload_stage_missing", retryable=False) from exc
        except OSError as exc:
            raise JobFailure("upload_stage_unavailable") from exc

        try:
            with file:
                location = storage_for_owner(asset.item.owner_id).save(asset, file)
        except DriveError as exc:
            Item.objects.filter(pk=asset.item_id).exclude(
                asset_storage="verified"
            ).update(asset_storage="pending" if exc.retryable else "failed")
            raise JobFailure(exc.code, retryable=exc.retryable) from exc
        except OSError as exc:
            raise JobFailure("upload_stage_unavailable") from exc
        if location.status != StorageLocation.Status.VERIFIED:
            raise JobFailure("upload_not_verified")

    Item.objects.filter(pk=asset.item_id).update(
        asset_storage="verified", source_fetch="not_applicable"
    )
    thumbnail_from_staging(asset, path)

    try:
        path.unlink(missing_ok=True)
    except OSError as exc:
        raise JobFailure("upload_stage_cleanup_failed") from exc
