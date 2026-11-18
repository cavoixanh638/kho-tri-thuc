from django.http import HttpResponseRedirect
from django.views.decorators.cache import never_cache
from ninja import Router, Schema, Status
from ninja.security import django_auth

from .drive import DriveError
from .models import DriveAccount
from .oauth import finish_connection, start_connection, token_cipher

router = Router(auth=django_auth, tags=["Google Drive"])


class IntegrationStatus(Schema):
    state: str
    display_name: str = ""


class ConnectResponse(Schema):
    authorization_url: str


class IntegrationError(Schema):
    code: str


@router.get("/status", response=IntegrationStatus)
def status(request):
    try:
        token_cipher()
    except DriveError:
        return {"state": "not_configured"}
    account = DriveAccount.objects.filter(owner=request.user).first()
    if not account:
        return {"state": "not_connected"}
    return {"state": account.state, "display_name": account.display_name}


@router.post("/connect", response={200: ConnectResponse, 503: IntegrationError})
def connect(request):
    try:
        return {"authorization_url": start_connection(request)}
    except DriveError as error:
        return Status(503, {"code": error.code})


@router.get("/callback")
@never_cache
def callback(request, state: str = "", code: str = ""):
    try:
        finish_connection(request, state, code)
        result = "connected"
    except DriveError as error:
        result = error.code
    response = HttpResponseRedirect(f"/?drive={result}")
    response["Referrer-Policy"] = "no-referrer"
    return response
