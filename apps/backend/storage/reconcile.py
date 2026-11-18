from dataclasses import dataclass, replace
from datetime import datetime
from http import HTTPStatus
from re import fullmatch

from catalog.models import RelatedItem
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from processing.models import DerivedContent

from .drive import DriveError
from .models import StorageLocation
from .service import BLOB_FIELDS, DRIVE_PROVIDER

RECONCILE_FIELDS = f"{BLOB_FIELDS},name,parents"


@dataclass(frozen=True, slots=True)
class ReconcileResult:
    status: str
    outcome: str
    detail: str = ""
    remote_name: str | None = None
    outside_root: bool | None = None
    revision: str = ""
    modified_at: datetime | None = None
    applied: bool = False


def _check_owner(location, account):
    if (
        location.provider != DRIVE_PROVIDER
        or account.owner_id != location.asset.item.owner_id
    ):
        raise DriveError("storage_owner_mismatch")


def probe_location(location, *, client, account):
    """Read Drive metadata without applying any catalog changes."""
    _check_owner(location, account)
    status = StorageLocation.Status
    file_id = location.provider_file_id
    if not file_id:
        return ReconcileResult(location.status, "unmapped")

    try:
        metadata = client.get_file(file_id, RECONCILE_FIELDS)
    except DriveError as error:
        if error.retryable:
            raise
        if error.status == HTTPStatus.NOT_FOUND:
            return ReconcileResult(
                status.INACCESSIBLE, "inaccessible", "not_found_or_no_permission"
            )
        if (
            error.status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN)
            or error.code == "drive_reauthorize"
        ):
            return ReconcileResult(status.INACCESSIBLE, "inaccessible", error.code)
        raise

    asset = location.asset
    if not isinstance(metadata, dict):
        raise DriveError("invalid_drive_metadata")
    properties = metadata.get("appProperties") or {}
    if (
        metadata.get("id") != file_id
        or not isinstance(properties, dict)
        or properties.get("kt_item_id") != str(asset.item_id)
        or properties.get("kt_asset_id") != str(asset.pk)
    ):
        return ReconcileResult(
            status.INACCESSIBLE, "identity_mismatch", "app_properties_unverified"
        )

    remote_name = metadata.get("name")
    parents = metadata.get("parents")
    outside_root = (
        account.root_folder_id not in parents
        if account.root_folder_id and isinstance(parents, list)
        else None
    )
    revision = str(metadata.get("version", ""))
    if not fullmatch(r"[0-9]{1,40}", revision):
        raise DriveError("invalid_drive_revision")

    modified_at = None
    if modified := metadata.get("modifiedTime"):
        try:
            modified_at = parse_datetime(modified)
        except (TypeError, ValueError):
            raise DriveError("invalid_drive_modified_time") from None
        if modified_at is None or timezone.is_naive(modified_at):
            raise DriveError("invalid_drive_modified_time")

    result_metadata = {
        "remote_name": remote_name if isinstance(remote_name, str) else None,
        "outside_root": outside_root,
        "revision": revision,
        "modified_at": modified_at,
    }
    if metadata.get("trashed") is True:
        return ReconcileResult(status.MISSING, "trashed", **result_metadata)

    try:
        size = int(metadata["size"])
        mime = metadata["mimeType"]
    except (KeyError, TypeError, ValueError):
        raise DriveError("invalid_drive_blob_metadata") from None
    if size < 0 or not isinstance(mime, str) or not mime:
        raise DriveError("invalid_drive_blob_metadata")

    remote_digest = metadata.get("sha256Checksum") or ""
    if not isinstance(remote_digest, str) or (
        remote_digest and not fullmatch(r"[0-9a-fA-F]{64}", remote_digest)
    ):
        raise DriveError("invalid_drive_sha256")
    trusted_digest = asset.sha256.lower()
    remote_digest = remote_digest.lower()

    if (
        (asset.size is not None and asset.size != size)
        or asset.mime != mime
        or (remote_digest and trusted_digest and remote_digest != trusted_digest)
    ):
        return ReconcileResult(status.FAILED, "content_changed", **result_metadata)
    if asset.size == size and (
        (remote_digest and remote_digest == trusted_digest)
        or (
            not remote_digest
            and location.status == status.VERIFIED
            and location.verified_at
            and location.provider_revision == revision
        )
    ):
        return ReconcileResult(status.VERIFIED, "verified", **result_metadata)
    return ReconcileResult(
        status.FAILED, "content_unverified", "sha256_unconfirmed", **result_metadata
    )


def _snapshot(location):
    asset = location.asset
    return (
        location.provider_file_id,
        location.status,
        location.verified_at,
        location.provider_revision,
        location.provider_modified_at,
        asset.item_id,
        asset.content_version,
        asset.size,
        asset.mime,
        asset.sha256,
    )


def _mark_derived_stale(asset):
    DerivedContent.objects.filter(
        asset=asset, status=DerivedContent.Status.ACTIVE
    ).update(status=DerivedContent.Status.STALE)
    RelatedItem.objects.filter(
        Q(item_a=asset.item_id) | Q(item_b=asset.item_id),
        status=RelatedItem.Status.ACTIVE,
    ).update(status=RelatedItem.Status.STALE)


def reconcile_location(location, *, client, account):
    """Apply one observation if its local input still matches the preflight snapshot."""
    expected = _snapshot(location)
    result = probe_location(location, client=client, account=account)
    status = StorageLocation.Status
    if result.outcome == "unmapped":
        return result

    with transaction.atomic():
        current = (
            StorageLocation.objects.select_related("asset__item")
            .select_for_update(of=("self", "asset"))
            .filter(pk=location.pk)
            .first()
        )
        if current is None:
            return ReconcileResult(location.status, "superseded")
        _check_owner(current, account)
        if _snapshot(current) != expected or (
            result.revision
            and current.provider_revision.isascii()
            and current.provider_revision.isdigit()
            and int(result.revision) < int(current.provider_revision)
        ):
            return ReconcileResult(current.status, "superseded")

        # A reservation can legitimately return 404 before its upload completes.
        if current.status == status.PENDING and result.outcome == "inaccessible":
            return replace(result, status=current.status)

        fields = {}
        if result.status != current.status:
            fields["status"] = result.status
        # Keep the last assessed revision when new metadata gives insufficient
        # evidence about its bytes. A later checksum can then assess it.
        if result.revision and result.outcome != "content_unverified":
            new_revision = result.revision != current.provider_revision
            if new_revision:
                fields["provider_revision"] = result.revision
            if (
                result.modified_at is not None
                and result.modified_at != current.provider_modified_at
            ):
                fields["provider_modified_at"] = result.modified_at
            if result.outcome == "content_changed" and (
                new_revision or current.status == status.VERIFIED
            ):
                asset = current.asset
                asset.content_version += 1
                asset.save(update_fields=["content_version"])
                _mark_derived_stale(asset)

        if not fields:
            return result
        if result.status == status.VERIFIED:
            fields["verified_at"] = timezone.now()
        StorageLocation.objects.filter(pk=current.pk).update(**fields)
        return replace(result, applied=True)
