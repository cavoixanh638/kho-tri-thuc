import json
from http import HTTPStatus

import google_auth_httplib2
import httplib2
from django.conf import settings
from google.auth.exceptions import RefreshError, TransportError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.file"
TOKEN_URI = "https://oauth2.googleapis.com/token"
FOLDER_MIME = "application/vnd.google-apps.folder"


class DriveError(Exception):
    def __init__(self, code, *, status=None, retryable=False):
        super().__init__(code)
        self.code = code
        self.status = status
        self.retryable = retryable


def drive_configured():
    return bool(
        settings.GOOGLE_DRIVE_CLIENT_ID
        and settings.GOOGLE_DRIVE_CLIENT_SECRET
        and settings.GOOGLE_DRIVE_REDIRECT_URI
        and settings.GOOGLE_DRIVE_TOKEN_KEY
    )


def drive_credentials(refresh_token):
    return Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=TOKEN_URI,
        client_id=settings.GOOGLE_DRIVE_CLIENT_ID,
        client_secret=settings.GOOGLE_DRIVE_CLIENT_SECRET,
        scopes=[DRIVE_SCOPE],
    )


def http_error(exc):
    status = exc.resp.status
    try:
        details = json.loads(exc.content).get("error", {}).get("errors", [])
        reason = details[0].get("reason") if details else None
    except (ValueError, TypeError, AttributeError):
        reason = None

    if status == HTTPStatus.UNAUTHORIZED:
        return DriveError("drive_reauthorize", status=status)
    if status == HTTPStatus.FORBIDDEN and reason in (
        "rateLimitExceeded",
        "userRateLimitExceeded",
    ):
        return DriveError("drive_rate_limited", status=status, retryable=True)
    if status == HTTPStatus.TOO_MANY_REQUESTS or status >= 500:
        return DriveError("drive_unavailable", status=status, retryable=True)
    if status == HTTPStatus.NOT_FOUND:
        return DriveError("drive_not_found", status=status)
    if status == HTTPStatus.FORBIDDEN and reason == "storageQuotaExceeded":
        return DriveError("drive_quota_exceeded", status=status)
    return DriveError("drive_request_failed", status=status)


class DriveClient:
    def __init__(self, credentials, *, on_reauthorize=None):
        transport = google_auth_httplib2.AuthorizedHttp(
            credentials, http=httplib2.Http(timeout=15)
        )
        self.api = build("drive", "v3", http=transport, cache_discovery=False)
        self.on_reauthorize = on_reauthorize

    def call(self, action):
        try:
            return action()
        except RefreshError as exc:
            if "invalid_grant" in str(exc):
                if self.on_reauthorize:
                    self.on_reauthorize()
                raise DriveError("drive_reauthorize") from None
            raise DriveError("drive_unavailable", retryable=True) from None
        except HttpError as exc:
            error = http_error(exc)
            if error.code == "drive_reauthorize" and self.on_reauthorize:
                self.on_reauthorize()
            raise error from None
        except (OSError, httplib2.HttpLib2Error, TransportError):
            raise DriveError("drive_unavailable", retryable=True) from None

    def execute(self, request):
        return self.call(request.execute)

    def account_user(self):
        result = self.execute(
            self.api.about().get(fields="user(permissionId,displayName)")
        )
        return result.get("user", {})

    def reserve_file_id(self):
        result = self.execute(
            self.api.files().generateIds(count=1, space="drive", type="files")
        )
        ids = result.get("ids", [])
        if not ids:
            raise DriveError("drive_missing_file_id", retryable=True)
        return ids[0]

    def get_file(self, file_id, fields):
        return self.execute(self.api.files().get(fileId=file_id, fields=fields))

    def find_root(self):
        parents = self.api.files()
        marker = "appProperties has { key='kt_root' and value='1' }"
        query = f"trashed = false and mimeType = '{FOLDER_MIME}' and {marker}"
        found = []
        page_token = None
        for _ in range(10):
            page = self.execute(
                parents.list(
                    q=query,
                    spaces="drive",
                    pageSize=2,
                    fields="nextPageToken,files(id)",
                    pageToken=page_token,
                )
            )
            found.extend(file["id"] for file in page.get("files", []))
            if len(found) > 1:
                raise DriveError("drive_root_ambiguous")
            page_token = page.get("nextPageToken")
            if not page_token:
                return found[0] if found else None
        raise DriveError("drive_root_lookup_incomplete", retryable=True)

    def ensure_root(self, root_id):
        fields = "id,mimeType,trashed,appProperties"
        try:
            root = self.get_file(root_id, fields)
        except DriveError as error:
            if error.status != HTTPStatus.NOT_FOUND:
                raise
            try:
                root = self.execute(
                    self.api.files().create(
                        body={
                            "id": root_id,
                            "name": "Kho Tri Thuc",
                            "mimeType": FOLDER_MIME,
                            "parents": ["root"],
                            "appProperties": {"kt_root": "1"},
                        },
                        fields=fields,
                    )
                )
            except DriveError as conflict:
                if conflict.status != HTTPStatus.CONFLICT:
                    raise
                root = self.get_file(root_id, fields)

        if (
            root.get("id") != root_id
            or root.get("mimeType") != FOLDER_MIME
            or root.get("trashed")
            or root.get("appProperties", {}).get("kt_root") != "1"
        ):
            raise DriveError("drive_root_unavailable")

    def upload_blob(self, stream, mime, metadata, *, resumable):
        media = MediaIoBaseUpload(
            stream, mimetype=mime, chunksize=8 * 1024 * 1024, resumable=resumable
        )
        request = self.api.files().create(body=metadata, media_body=media, fields="id")
        if not resumable:
            return self.execute(request)
        response = None
        while response is None:
            _, response = self.call(request.next_chunk)
        return response
