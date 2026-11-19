from datetime import datetime
from typing import Literal
from uuid import UUID

from catalog.models import Item
from django.shortcuts import get_object_or_404
from ninja import Router, Schema, Status
from ninja.security import django_auth
from storage.models import KnowledgeExport

from .knowledge import snapshot
from .knowledge_sync import configure, request_sync

router = Router(auth=django_auth, tags=["Knowledge export"])


class Options(Schema):
    enabled: bool
    format: Literal["markdown", "text"]


class Error(Schema):
    error: str


class ExportStatus(Schema):
    enabled: bool
    format: str
    status: str
    source_version: str
    exported_version: str
    stale: bool
    truncated: bool
    last_error: str
    last_synced_at: datetime | None
    url: str | None


def status(item):
    record = KnowledgeExport.objects.filter(item=item).first()
    if record is None:
        return {
            "enabled": False,
            "format": "markdown",
            "status": "disabled",
            "source_version": "",
            "exported_version": "",
            "stale": False,
            "truncated": False,
            "last_error": "",
            "last_synced_at": None,
            "url": None,
        }
    current = snapshot(item.pk, record.format)
    stale = bool(
        record.enabled
        and (not record.exported_version or record.exported_version != current.version)
    )
    state = record.status
    if stale and state == "synced":
        state = "stale"
    available = (
        record.enabled
        and not item.deleted_at
        and state == "synced"
        and record.provider_file_id
    )
    return {
        "enabled": record.enabled,
        "format": record.format,
        "status": state,
        "source_version": current.version,
        "exported_version": record.exported_version,
        "stale": stale,
        "truncated": current.truncated,
        "last_error": record.last_error,
        "last_synced_at": record.last_synced_at,
        "url": "https://drive.google.com/open?id=" + record.provider_file_id
        if available
        else None,
    }


@router.get("/items/{item_id}/knowledge-export", response=ExportStatus)
def read_export(request, item_id: UUID):
    return status(get_object_or_404(Item, pk=item_id, owner=request.user))


@router.post(
    "/items/{item_id}/knowledge-export", response={200: ExportStatus, 409: Error}
)
def change_export(request, item_id: UUID, payload: Options):
    item = get_object_or_404(Item, pk=item_id, owner=request.user)
    if item.deleted_at and payload.enabled:
        return Status(409, {"error": "item_deleted"})
    try:
        configure(item, enabled=payload.enabled, format=payload.format)
    except ValueError as error:
        return Status(409, {"error": str(error)})
    return status(item)


@router.post("/items/{item_id}/knowledge-export/retry", response=ExportStatus)
def retry_export(request, item_id: UUID):
    item = get_object_or_404(Item, pk=item_id, owner=request.user)
    request_sync(item.pk, force=True)
    return status(item)
