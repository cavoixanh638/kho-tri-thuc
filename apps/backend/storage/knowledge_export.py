"""Drive blob adapter for opt-in knowledge derivatives; never modifies originals."""

import hashlib
from http import HTTPStatus
from io import BytesIO

from googleapiclient.http import MediaIoBaseUpload

from .drive import FOLDER_MIME, DriveError
from .models import DriveAccount

FIELDS = "id,mimeType,size,sha256Checksum,md5Checksum,trashed,appProperties"


class DriveKnowledge:
    def __init__(self, client, account):
        self.client, self.account = client, account

    def reserve(self):
        return self.client.reserve_file_id()

    def folder(self):
        account = self.account
        if not account.knowledge_folder_id:
            root = account.root_folder_id.replace("\\", "\\\\").replace("'", "\\'")
            result = self.client.execute(
                self.client.api.files().list(
                    q=f"'{root}' in parents and trashed=false and appProperties has {{ key='kt_index' and value='1' }}",
                    spaces="drive",
                    pageSize=2,
                    fields="nextPageToken,files(id)",
                )
            )
            found = result.get("files", [])
            if len(found) > 1 or result.get("nextPageToken"):
                raise DriveError("knowledge_folder_ambiguous")
            candidate = found[0]["id"] if found else self.reserve()
            DriveAccount.objects.filter(pk=account.pk, knowledge_folder_id="").update(
                knowledge_folder_id=candidate
            )
            account.refresh_from_db(fields=["knowledge_folder_id"])
        file_id = account.knowledge_folder_id
        fields = "id,mimeType,trashed,parents,appProperties"
        try:
            folder = self.client.get_file(file_id, fields)
        except DriveError as error:
            if error.status != HTTPStatus.NOT_FOUND:
                raise
            try:
                folder = self.client.execute(
                    self.client.api.files().create(
                        body={
                            "id": file_id,
                            "name": "ChatGPT_Index",
                            "mimeType": FOLDER_MIME,
                            "parents": [account.root_folder_id],
                            "appProperties": {"kt_index": "1"},
                        },
                        fields=fields,
                    )
                )
            except DriveError as conflict:
                if conflict.status != HTTPStatus.CONFLICT:
                    raise
                folder = self.client.get_file(file_id, fields)
        if (
            folder.get("id") != file_id
            or folder.get("mimeType") != FOLDER_MIME
            or folder.get("trashed")
            or account.root_folder_id not in folder.get("parents", [])
            or folder.get("appProperties", {}).get("kt_index") != "1"
        ):
            raise DriveError("knowledge_folder_mismatch")
        return file_id

    def read(self, file_id, item_id):
        remote = self.client.get_file(file_id, FIELDS)
        properties = remote.get("appProperties", {})
        if (
            remote.get("id") != file_id
            or properties.get("kt_knowledge") != "1"
            or properties.get("kt_item_id") != str(item_id)
        ):
            raise DriveError("knowledge_identity_mismatch")
        return remote

    @staticmethod
    def matches(remote, body, mime, version):
        sha = hashlib.sha256(body).hexdigest()
        md5 = hashlib.md5(body, usedforsecurity=False).hexdigest()
        checksum = remote.get("sha256Checksum") or remote.get("md5Checksum")
        return bool(
            not remote.get("trashed")
            and remote.get("mimeType") == mime
            and int(remote.get("size", -1)) == len(body)
            and checksum
            and (not remote.get("sha256Checksum") or remote["sha256Checksum"] == sha)
            and (not remote.get("md5Checksum") or remote["md5Checksum"] == md5)
            and remote.get("appProperties", {}).get("kt_source_version") == version
        )

    def save(self, record, body, version):
        file_id = record.provider_file_id
        mime, extension = (
            ("text/markdown", "md")
            if record.format == "markdown"
            else ("text/plain", "txt")
        )
        metadata = {
            "name": f"Tri thuc - {record.item_id}.{extension}",
            "mimeType": mime,
            "appProperties": {
                "kt_knowledge": "1",
                "kt_item_id": str(record.item_id),
                "kt_source_version": version,
            },
        }
        try:
            remote = self.read(file_id, record.item_id)
        except DriveError as error:
            if error.status != HTTPStatus.NOT_FOUND:
                raise
            try:
                self.client.upload_blob(
                    BytesIO(body),
                    mime,
                    {**metadata, "id": file_id, "parents": [self.folder()]},
                    resumable=False,
                )
            except DriveError as conflict:
                if conflict.status != HTTPStatus.CONFLICT:
                    raise
            remote = self.read(file_id, record.item_id)
        if not self.matches(remote, body, mime, version):
            # A recovered lost response can leave an older revision at this ID.
            self.client.execute(
                self.client.api.files().update(
                    fileId=file_id,
                    body={**metadata, "trashed": False},
                    media_body=MediaIoBaseUpload(
                        BytesIO(body), mimetype=mime, resumable=False
                    ),
                    fields="id",
                )
            )
            remote = self.read(file_id, record.item_id)
        if not self.matches(remote, body, mime, version):
            raise DriveError("knowledge_checksum_mismatch", retryable=True)

    def trash(self, record):
        if not record.provider_file_id:
            return
        try:
            remote = self.read(record.provider_file_id, record.item_id)
        except DriveError as error:
            if error.status == HTTPStatus.NOT_FOUND:
                return
            raise
        if not remote.get("trashed"):
            self.client.execute(
                self.client.api.files().update(
                    fileId=record.provider_file_id,
                    body={"trashed": True},
                    fields="id",
                )
            )
        if not self.read(record.provider_file_id, record.item_id).get("trashed"):
            raise DriveError("knowledge_withdraw_failed", retryable=True)
