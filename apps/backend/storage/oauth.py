import secrets
import time

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from google_auth_oauthlib.flow import Flow
from oauthlib.oauth2 import OAuth2Error
from requests import RequestException

from jobs.models import Job

from .drive import (
    DRIVE_SCOPE,
    TOKEN_URI,
    DriveClient,
    DriveError,
    drive_configured,
    drive_credentials,
)
from .models import DriveAccount

SESSION_KEY = "drive_oauth_pending"
STATE_TTL_SECONDS = 600
AUTHORIZATION_URI = "https://accounts.google.com/o/oauth2/v2/auth"


def token_cipher():
    if not drive_configured():
        raise DriveError("drive_not_configured")
    try:
        return Fernet(settings.GOOGLE_DRIVE_TOKEN_KEY.encode("ascii"))
    except (ValueError, UnicodeError):
        raise DriveError("drive_not_configured") from None


def oauth_flow(*, state=None, verifier=None):
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_DRIVE_CLIENT_ID,
                "client_secret": settings.GOOGLE_DRIVE_CLIENT_SECRET,
                "auth_uri": AUTHORIZATION_URI,
                "token_uri": TOKEN_URI,
            }
        },
        scopes=[DRIVE_SCOPE],
        redirect_uri=settings.GOOGLE_DRIVE_REDIRECT_URI,
        state=state,
        code_verifier=verifier,
        autogenerate_code_verifier=verifier is None,
    )


def start_connection(request):
    token_cipher()
    flow = oauth_flow()
    url, state = flow.authorization_url(access_type="offline", prompt="consent")
    request.session[SESSION_KEY] = {
        "owner": str(request.user.pk),
        "state": state,
        "verifier": flow.code_verifier,
        "expires_at": time.time() + STATE_TTL_SECONDS,
    }
    return url


def finish_connection(request, state, code):
    pending = request.session.pop(SESSION_KEY, None)
    if (
        not pending
        or pending["owner"] != str(request.user.pk)
        or not secrets.compare_digest(state.encode(), pending["state"].encode())
        or time.time() >= pending["expires_at"]
        or not code
    ):
        raise DriveError("drive_callback_invalid")

    cipher = token_cipher()
    flow = oauth_flow(state=state, verifier=pending["verifier"])
    try:
        flow.fetch_token(code=code, timeout=15)
        credentials = flow.credentials
    except (OAuth2Error, RequestException, ValueError, Warning):
        raise DriveError("drive_exchange_failed") from None

    scopes = credentials.granted_scopes or credentials.scopes or []
    if not credentials.refresh_token or set(scopes) != {DRIVE_SCOPE}:
        raise DriveError("drive_missing_consent")

    client = DriveClient(credentials)
    drive_user = client.account_user()
    google_user_id = drive_user.get("permissionId")
    if not google_user_id:
        raise DriveError("drive_missing_identity")

    account, _ = DriveAccount.objects.get_or_create(
        owner=request.user,
        defaults={"google_user_id": google_user_id},
    )
    if account.google_user_id != google_user_id:
        raise DriveError("drive_account_mismatch")
    if not account.root_folder_id:
        candidate = client.find_root() or client.reserve_file_id()
        DriveAccount.objects.filter(pk=account.pk, root_folder_id="").update(
            root_folder_id=candidate
        )
        account.refresh_from_db(fields=["root_folder_id"])

    client.ensure_root(account.root_folder_id)
    with transaction.atomic():
        DriveAccount.objects.filter(pk=account.pk).update(
            display_name=drive_user.get("displayName", "")[:255],
            refresh_token_ciphertext=cipher.encrypt(
                credentials.refresh_token.encode()
            ).decode(),
            state=DriveAccount.State.CONNECTED,
            connected_at=timezone.now(),
        )
        Job.objects.filter(
            item__owner=request.user,
            kind__in=["upload_asset", "export_knowledge"],
            state=Job.State.FAILED,
            error_code__in=[
                "drive_not_connected",
                "drive_not_configured",
                "drive_reauthorize",
            ],
        ).update(
            state=Job.State.RETRY,
            attempt=0,
            retry_at=timezone.now(),
            completed_at=None,
            error_code="",
        )


def client_for_owner(owner_id):
    account = DriveAccount.objects.filter(
        owner_id=owner_id, state=DriveAccount.State.CONNECTED
    ).first()
    if not account:
        raise DriveError("drive_not_connected")

    ciphertext = account.refresh_token_ciphertext

    def mark_reauthorize():
        DriveAccount.objects.filter(
            pk=account.pk, refresh_token_ciphertext=ciphertext
        ).update(state=DriveAccount.State.REAUTHORIZE)

    try:
        refresh_token = token_cipher().decrypt(ciphertext.encode()).decode()
    except (InvalidToken, UnicodeError):
        mark_reauthorize()
        raise DriveError("drive_reauthorize") from None
    return DriveClient(
        drive_credentials(refresh_token), on_reauthorize=mark_reauthorize
    ), account
