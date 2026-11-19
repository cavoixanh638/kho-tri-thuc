"""Immutable, resumable Drive copies of consistent PostgreSQL backup bundles."""

import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from http import HTTPStatus
from pathlib import Path

from backup import CHECKSUMS, DUMP, MANIFEST, BackupError, verify_bundle
from googleapiclient.http import MediaIoBaseDownload

FILES = (DUMP, MANIFEST, CHECKSUMS)
LIMIT = 512 * 1024 * 1024
FOLDER = "application/vnd.google-apps.folder"
FIELDS = "id,size,mimeType,sha256Checksum,md5Checksum,trashed,appProperties,parents"


def digest(path, algorithm="sha256"):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, algorithm).hexdigest()


def _write_state(path, data):
    pending = path.with_suffix(".pending")
    with pending.open("w", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    pending.replace(path)


def pack(bundle, archive):
    verify_bundle(bundle)
    if sum((bundle / name).stat().st_size for name in FILES) > LIMIT:
        raise BackupError("Backup bundle exceeds the Drive copy limit.")
    if archive.exists():
        raise BackupError("Choose a new archive filename.")
    pending = archive.with_suffix(".pending")
    try:
        with zipfile.ZipFile(pending, "w", compression=zipfile.ZIP_STORED) as output:
            for name in FILES:
                entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                entry.external_attr = 0o600 << 16
                with (
                    (bundle / name).open("rb") as source,
                    output.open(entry, "w") as target,
                ):
                    shutil.copyfileobj(source, target, length=1024 * 1024)
        with pending.open("r+b") as stream:
            os.fsync(stream.fileno())
        pending.replace(archive)
    finally:
        pending.unlink(missing_ok=True)
    return digest(archive)


def unpack(archive, destination):
    if destination.exists():
        raise BackupError("Choose a new restored bundle directory.")
    with (
        zipfile.ZipFile(archive) as source,
        tempfile.TemporaryDirectory(
            prefix=".kt-unpack-",
            dir=destination.parent,
        ) as scratch,
    ):
        entries = source.infolist()
        if len(entries) != len(FILES) or {entry.filename for entry in entries} != set(
            FILES
        ):
            raise BackupError("Unexpected files in backup archive.")
        if any(entry.is_dir() or entry.flag_bits & 1 for entry in entries):
            raise BackupError("Unsupported backup archive entries.")
        if sum(entry.file_size for entry in entries) > LIMIT:
            raise BackupError("Backup archive is too large.")
        staging = Path(scratch) / "bundle"
        staging.mkdir()
        for entry in entries:
            bound = {DUMP: LIMIT, MANIFEST: 16 * 1024 * 1024, CHECKSUMS: 4096}[
                entry.filename
            ]
            if entry.file_size > bound:
                raise BackupError("Backup archive member exceeds its limit.")
            with (
                source.open(entry) as original,
                (staging / entry.filename).open("wb") as target,
            ):
                remaining = entry.file_size
                while chunk := original.read(min(1024 * 1024, remaining + 1)):
                    remaining -= len(chunk)
                    if remaining < 0:
                        raise BackupError("Backup archive member size mismatch.")
                    target.write(chunk)
                if remaining:
                    raise BackupError("Backup archive member was truncated.")
        verify_bundle(staging)
        staging.rename(destination)


class _BoundedSink:
    def __init__(self, stream, size):
        self.stream, self.size, self.written = stream, size, 0

    def write(self, chunk):
        if self.written + len(chunk) > self.size:
            raise BackupError("Drive download exceeds the expected size.")
        count = self.stream.write(chunk)
        self.written += count
        return count


def download(client, file_id, destination, size, sha256):
    if not 0 < size <= LIMIT:
        raise BackupError("Drive download size is outside the allowed bound.")
    if destination.exists():
        raise BackupError("Choose a new Drive download filename.")
    pending = destination.with_suffix(".pending")
    try:
        request = client.api.files().get_media(fileId=file_id)
        with pending.open("wb") as stream:
            sink = _BoundedSink(stream, size)
            request = MediaIoBaseDownload(sink, request, chunksize=1024 * 1024)
            for _ in range(size // (1024 * 1024) + 2):
                _, done = client.call(request.next_chunk)
                if done:
                    if sink.written != size:
                        raise BackupError("Drive download was truncated.")
                    break
            else:
                raise BackupError(
                    "Drive download did not finish within its chunk bound."
                )
            stream.flush()
            os.fsync(stream.fileno())
        if digest(pending) != sha256:
            raise BackupError("Drive download checksum mismatch.")
        pending.replace(destination)
    finally:
        pending.unlink(missing_ok=True)


class DriveBackups:
    """Keep pre-generated IDs in a private receipt before any remote create."""

    def __init__(self, client, root_folder, state_directory):
        self.client, self.root = client, root_folder
        self.directory = state_directory
        state_directory.mkdir(parents=True, exist_ok=True)
        self.state_path = state_directory / "drive-backups.json"
        if self.state_path.exists():
            self.state = json.loads(self.state_path.read_text(encoding="utf-8"))
            if self.state.get("root_folder") != root_folder:
                raise BackupError("Backup receipt belongs to another Drive root.")
        else:
            self.state = {"root_folder": root_folder, "files": {}}
        self.folder = self._folder()

    def _save(self):
        _write_state(self.state_path, self.state)

    def _lookup_folder(self):
        root = self.root.replace("\\", "\\\\").replace("'", "\\'")
        found = self.client.execute(
            self.client.api.files().list(
                q=f"'{root}' in parents and trashed = false and mimeType = '{FOLDER}' "
                "and appProperties has { key='kt_backups' and value='1' }",
                spaces="drive",
                pageSize=2,
                fields="nextPageToken,files(id)",
            )
        )
        files = found.get("files", [])
        if found.get("nextPageToken") or len(files) > 1:
            raise BackupError("Drive backup folder lookup is ambiguous.")
        return files[0]["id"] if files else None

    def _folder(self):
        from storage.drive import DriveError

        candidate = self.state.get("folder_id")
        if not candidate:
            candidate = self._lookup_folder() or self.client.reserve_file_id()
            self.state["folder_id"] = candidate
            self._save()
        try:
            folder = self.client.get_file(
                candidate, "id,mimeType,trashed,appProperties,parents"
            )
        except DriveError as error:
            if error.status != HTTPStatus.NOT_FOUND:
                raise
            try:
                folder = self.client.execute(
                    self.client.api.files().create(
                        body={
                            "id": candidate,
                            "name": "System_Backups",
                            "mimeType": FOLDER,
                            "parents": [self.root],
                            "appProperties": {"kt_backups": "1"},
                        },
                        fields="id,mimeType,trashed,appProperties,parents",
                    )
                )
            except DriveError as conflict:
                if conflict.status != HTTPStatus.CONFLICT:
                    raise
                folder = self.client.get_file(
                    candidate, "id,mimeType,trashed,appProperties,parents"
                )
        if (
            folder.get("id") != candidate
            or folder.get("mimeType") != FOLDER
            or folder.get("trashed")
            or self.root not in folder.get("parents", [])
            or folder.get("appProperties", {}).get("kt_backups") != "1"
        ):
            raise BackupError("Drive backup folder is unavailable.")
        return candidate

    def _verify(self, archive, file_id, sha256):
        remote = self.client.get_file(file_id, FIELDS)
        if (
            remote.get("id") != file_id
            or remote.get("trashed")
            or self.folder not in remote.get("parents", [])
            or remote.get("mimeType") != "application/zip"
            or int(remote.get("size", -1)) != archive.stat().st_size
            or remote.get("appProperties", {}).get("kt_backup") != "1"
            or remote.get("appProperties", {}).get("kt_bundle_sha256") != sha256
        ):
            raise BackupError("Drive backup identity mismatch.")
        sha, md5 = remote.get("sha256Checksum"), remote.get("md5Checksum")
        if (
            (not sha and not md5)
            or (sha and sha != sha256)
            or (md5 and md5 != digest(archive, "md5"))
        ):
            raise BackupError("Drive backup checksum mismatch.")
        return remote

    def upload(self, archive):
        from storage.drive import DriveError

        sha256 = digest(archive)
        if not 0 < archive.stat().st_size <= LIMIT:
            raise BackupError("Backup archive size is outside the allowed bound.")
        file_id = self.state["files"].get(sha256)
        if not file_id:
            file_id = self.client.reserve_file_id()
            self.state["files"][sha256] = file_id
            self._save()
        try:
            self._verify(archive, file_id, sha256)
        except DriveError as error:
            if error.status != HTTPStatus.NOT_FOUND:
                raise
            try:
                with archive.open("rb") as stream:
                    self.client.upload_blob(
                        stream,
                        "application/zip",
                        {
                            "id": file_id,
                            "name": f"kho-tri-thuc-backup-{sha256[:16]}.zip",
                            "parents": [self.folder],
                            "appProperties": {
                                "kt_backup": "1",
                                "kt_bundle_sha256": sha256,
                            },
                        },
                        resumable=True,
                    )
            except DriveError as conflict:
                if conflict.status != HTTPStatus.CONFLICT:
                    raise
            self._verify(archive, file_id, sha256)
        return file_id
