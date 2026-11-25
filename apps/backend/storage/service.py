import hashlib
from dataclasses import dataclass
from datetime import datetime
from http import HTTPStatus
from typing import BinaryIO, Protocol
from urllib.parse import urlencode

from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .drive import DriveError
from .models import Asset, StorageLocation
from .oauth import client_for_owner

DRIVE_PROVIDER = "google_drive"
BLOB_FIELDS = "id,size,sha256Checksum,md5Checksum,mimeType,version,headRevisionId,modifiedTime,trashed,appProperties"


@dataclass(frozen=True, slots=True)
class RemoteFile:
    file_id: str
    size: int
    mime: str
    modified_at: datetime | None
    revision: str
    sha256: str
    md5: str
    head_revision_id: str = ""

    def accepts_version(self, previous):
        if self.revision and self.revision == previous:
            return True
        # Drive file.version includes metadata-only changes after upload. For
        # binary files with a headRevisionId, allow only forward version drift.
        return bool(self.head_revision_id and previous.isascii() and previous.isdigit()
                    and self.revision.isascii() and self.revision.isdigit()
                    and int(self.revision) > int(previous))

    def same_read_source(self, before):
        if not before.head_revision_id:
            return self == before
        return (self.accepts_version(before.revision)
                and self.head_revision_id == before.head_revision_id
                and self.file_id == before.file_id and self.size == before.size
                and self.mime == before.mime and self.sha256 == before.sha256)


class StoragePort(Protocol):
    def save(self, asset: Asset, stream: BinaryIO) -> StorageLocation: ...
    def stat(self, asset: Asset) -> RemoteFile: ...
    def verify(self, asset: Asset) -> StorageLocation: ...
    def open(self, asset: Asset) -> str: ...
    def read_range(self, asset: Asset, start: int, end: int) -> bytes: ...


def fingerprint(stream):
    sha256 = hashlib.sha256()
    md5 = hashlib.md5(usedforsecurity=False)
    size = 0
    stream.seek(0)
    while chunk := stream.read(1024 * 1024):
        sha256.update(chunk)
        md5.update(chunk)
        size += len(chunk)
    stream.seek(0)
    return size, sha256.hexdigest(), md5.hexdigest()


class DriveStorage:
    # Every read_range verifies download permission and the full asset SHA in
    # current Drive metadata, then checks that the binary did not change.
    verifies_range_source = True

    def __init__(self, client, account):
        self.client = client
        self.account = account

    def _check_owner(self, asset):
        if asset.item.owner_id != self.account.owner_id:
            raise DriveError("storage_owner_mismatch")

    def _locate(self, asset):
        self._check_owner(asset)
        location = asset.locations.filter(provider=DRIVE_PROVIDER).first()
        if not location or not location.provider_file_id:
            raise DriveError("storage_location_missing")
        return location

    def _reserve(self, asset):
        self._check_owner(asset)
        location, _ = StorageLocation.objects.get_or_create(
            asset=asset, provider=DRIVE_PROVIDER
        )
        if not location.provider_file_id:
            candidate = self.client.reserve_file_id()
            StorageLocation.objects.filter(pk=location.pk).filter(
                Q(provider_file_id__isnull=True) | Q(provider_file_id="")
            ).update(provider_file_id=candidate)
            location.refresh_from_db(fields=["provider_file_id"])
        return location

    def _read(self, asset, file_id):
        content = self.client.get_file(file_id, BLOB_FIELDS)
        properties = content.get("appProperties") or {}
        if (
            content.get("id") != file_id
            or content.get("trashed")
            or properties.get("kt_item_id") != str(asset.item_id)
            or properties.get("kt_asset_id") != str(asset.pk)
            or "size" not in content
            or "mimeType" not in content
        ):
            raise DriveError("storage_identity_mismatch")
        return RemoteFile(
            file_id=file_id,
            size=int(content["size"]),
            mime=content["mimeType"],
            modified_at=parse_datetime(content["modifiedTime"])
            if content.get("modifiedTime")
            else None,
            revision=str(content.get("version", "")),
            sha256=content.get("sha256Checksum", ""),
            md5=content.get("md5Checksum", ""),
            head_revision_id=content.get("headRevisionId", ""),
        )

    def _record_verified(self, asset, location, remote, *, md5=""):
        if (
            asset.size != remote.size
            or asset.mime != remote.mime
            or (remote.sha256 and asset.sha256 != remote.sha256)
            or (remote.md5 and md5 and remote.md5 != md5)
        ):
            raise DriveError("storage_checksum_mismatch")

        location.status = StorageLocation.Status.VERIFIED
        location.verified_at = timezone.now()
        location.provider_modified_at = remote.modified_at
        location.provider_revision = remote.revision
        location.save(
            update_fields=[
                "status",
                "verified_at",
                "provider_modified_at",
                "provider_revision",
            ]
        )
        return location

    def save(self, asset, stream):
        self._check_owner(asset)
        size, sha256, md5 = fingerprint(stream)
        if size != asset.size or sha256 != asset.sha256:
            raise DriveError("storage_input_changed")
        location = self._reserve(asset)
        file_id = location.provider_file_id
        try:
            remote = self._read(asset, file_id)
        except DriveError as error:
            if error.status != HTTPStatus.NOT_FOUND:
                raise
            try:
                self.client.upload_blob(
                    stream,
                    asset.mime,
                    {
                        "id": file_id,
                        "name": asset.original_filename,
                        "parents": [self.account.root_folder_id],
                        "appProperties": {
                            "kt_item_id": str(asset.item_id),
                            "kt_asset_id": str(asset.pk),
                        },
                    },
                    resumable=size > 0,
                )
            except DriveError as conflict:
                if conflict.status != HTTPStatus.CONFLICT:
                    raise
            remote = self._read(asset, file_id)
        return self._record_verified(asset, location, remote, md5=md5)

    def stat(self, asset):
        location = self._locate(asset)
        return self._read(asset, location.provider_file_id)

    def verify(self, asset):
        location = self._locate(asset)
        return self._record_verified(
            asset, location, self._read(asset, location.provider_file_id)
        )

    def open(self, asset):
        location = self._locate(asset)
        if location.status != StorageLocation.Status.VERIFIED:
            raise DriveError("storage_not_verified")
        self.verify(asset)
        return "https://drive.google.com/open?" + urlencode(
            {"id": location.provider_file_id}
        )

    def read_range(self, asset, start, end):
        """Fail closed if the verified original changes around a bounded read.

        Bind each slice to the verified asset SHA and to a single binary head
        revision across the read. Drive may advance the metadata version even
        when the binary has not changed. Legacy metadata with no head revision
        keeps the strict version check. Viewing does not update the catalogue.
        """
        location = self._locate(asset)
        if location.status != StorageLocation.Status.VERIFIED:
            raise DriveError("storage_not_verified")
        before = self._read(asset, location.provider_file_id)
        if (
            not asset.sha256
            or not before.sha256
            or not before.revision
            or before.size != asset.size
            or before.mime != asset.mime
            or before.sha256 != asset.sha256
            or not before.accepts_version(location.provider_revision)
        ):
            raise DriveError("viewer_source_changed")
        payload = self.client.read_blob_range(before.file_id, start, end, before.size)
        after = self._read(asset, location.provider_file_id)
        if not after.same_read_source(before):
            raise DriveError("viewer_source_changed")
        if len(payload) != end - start + 1:
            raise DriveError("viewer_range_size_mismatch")
        return payload


def storage_for_owner(owner_id) -> StoragePort:
    client, account = client_for_owner(owner_id)
    return DriveStorage(client, account)
