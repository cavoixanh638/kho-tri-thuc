from datetime import datetime
from typing import Literal
from uuid import UUID

from catalog.models import Item
from django.http import Http404
from ninja import Query, Router, Schema, Status
from ninja.security import django_auth
from pydantic import AwareDatetime, Field

from .models import CaptureEvent
from .services import (
    MAX_TEXT_LENGTH,
    MAX_URL_LENGTH,
    CaptureSubmission,
    InvalidCapture,
    submit_capture,
)

router = Router(auth=django_auth, tags=["Captures"])


class CaptureRequest(Schema):
    kind: Literal["link", "text"]
    url: str = Field(default="", max_length=MAX_URL_LENGTH)
    text: str = Field(default="", max_length=MAX_TEXT_LENGTH)
    source_channel: Literal["web", "android", "windows", "share"] = "web"
    client_sent_at: AwareDatetime | None = None


class CaptureReceipt(Schema):
    capture_id: UUID
    item_id: UUID
    received_at: datetime
    state: Literal["received"]


class CaptureSummary(Schema):
    capture_id: UUID
    item_id: UUID
    received_at: datetime
    raw_kind: str
    raw_text: str
    original_url: str
    source_channel: str
    state: str

    @staticmethod
    def resolve_capture_id(event):
        return event.pk

    @staticmethod
    def resolve_received_at(event):
        return event.server_received_at

    @staticmethod
    def resolve_state(event):
        return event.status


class CapturePage(Schema):
    results: list[CaptureSummary]
    next_offset: int | None


class CaptureError(Schema):
    code: str


class HistoryQuery(Schema):
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0, le=2**31 - 1)
    received_from: AwareDatetime | None = None
    received_before: AwareDatetime | None = None


@router.post(
    "/captures", response={200: CaptureReceipt, 201: CaptureReceipt, 422: CaptureError}
)
def create_capture(request, payload: CaptureRequest):
    submission = CaptureSubmission(
        **payload.model_dump(), idempotency_key=request.headers.get("Idempotency-Key")
    )
    try:
        event, created = submit_capture(request.auth, submission)
    except InvalidCapture as error:
        return Status(422, {"code": error.code})

    return Status(
        201 if created else 200,
        {
            "capture_id": event.pk,
            "item_id": event.item_id,
            "received_at": event.server_received_at,
            "state": "received",
        },
    )


def _history(events, query):
    if query.received_from is not None:
        events = events.filter(server_received_at__gte=query.received_from)
    if query.received_before is not None:
        events = events.filter(server_received_at__lt=query.received_before)
    end = query.offset + query.limit
    rows = list(events.order_by("-server_received_at", "pk")[query.offset : end + 1])
    return {
        "results": rows[: query.limit],
        "next_offset": end if len(rows) > query.limit else None,
    }


@router.get("/captures", response=CapturePage)
def capture_history(request, query: Query[HistoryQuery]):
    return _history(CaptureEvent.objects.filter(owner=request.auth), query)


@router.get("/items/{item_id}/captures", response=CapturePage)
def item_capture_history(request, item_id: UUID, query: Query[HistoryQuery]):
    if not Item.objects.filter(pk=item_id, owner=request.auth).exists():
        raise Http404
    return _history(
        CaptureEvent.objects.filter(owner=request.auth, item_id=item_id), query
    )
