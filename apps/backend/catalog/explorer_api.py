from typing import Literal
from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import Router, Schema, Status
from ninja.security import django_auth
from pydantic import Field

from . import explorer
from .models import Topic

router = Router(tags=["Knowledge explorer"], auth=django_auth)


@router.get("/explorer/find", response=dict)
def find_notes(request, q: str = Field(default="", max_length=200)):
    query = explorer.item_query(request.user.pk)
    if q.strip():
        from django.db.models import Q
        query = query.filter(Q(title__icontains=q.strip()) | Q(note__icontains=q.strip()))
    return {"results": [explorer.summarize(row) for row in query.order_by("title", "id")[:20]]}


class Placement(Schema):
    action: Literal["move", "add", "remove"]
    folder_id: int | None = Field(default=None, ge=1)
    expected_version: int = Field(ge=0, strict=True)


class Structure(Schema):
    parent_item_id: UUID | None = None
    sort_order: int = Field(default=0, ge=0, le=1_000_000)
    expected_version: int = Field(ge=0, strict=True)


class NewNote(Schema):
    text: str = Field(min_length=1, max_length=65536)
    title: str = Field(default="", max_length=512)
    home_topic_id: int | None = Field(default=None, ge=1)
    parent_item_id: UUID | None = None


def failure(exc):
    code = str(exc)
    return Status(409 if code == "structure_conflict" else 404 if code.startswith("unknown_") else 422, {"code": code})


@router.get("/explorer/children", response={200: dict, 404: dict, 422: dict})
def read_children(request, folder_id: int | None = None, parent_item_id: UUID | None = None, unfiled: bool = False,
                  offset: int = Field(default=0, ge=0, le=1_000_000), limit: int = Field(default=50, ge=1, le=100)):
    try:
        return explorer.children(request.user.pk, folder_id=folder_id, parent_item_id=parent_item_id, unfiled=unfiled, offset=offset, limit=limit)
    except explorer.ExplorerError as exc:
        return failure(exc)


@router.get("/items/{item_id}/placement", response={200: dict, 404: dict})
def read_placement(request, item_id: UUID):
    try:
        return explorer.placement(explorer.active_item(request.user.pk, item_id))
    except explorer.ExplorerError as exc:
        return failure(exc)


@router.patch("/items/{item_id}/placement", response={200: dict, 404: dict, 409: dict, 422: dict})
def change_placement(request, item_id: UUID, body: Placement):
    try:
        return explorer.place(request.user.pk, item_id, **body.model_dump())
    except explorer.ExplorerError as exc:
        return failure(exc)


@router.get("/items/{item_id}/structure", response={200: dict, 404: dict})
def read_structure(request, item_id: UUID):
    try:
        return explorer.structure_info(request.user.pk, item_id)
    except explorer.ExplorerError as exc:
        return failure(exc)


@router.patch("/items/{item_id}/structure", response={200: dict, 404: dict, 409: dict, 422: dict})
def change_structure(request, item_id: UUID, body: Structure):
    try:
        return explorer.structure(request.user.pk, item_id, **body.model_dump())
    except explorer.ExplorerError as exc:
        return failure(exc)


@router.post("/explorer/notes", response={200: dict, 201: dict, 404: dict, 422: dict})
def create_note(request, body: NewNote):
    from ingestion.services import InvalidCapture
    try:
        event, created = explorer.create_note(request.user, text=body.text, title_text=body.title, home_topic_id=body.home_topic_id,
                                             parent_item_id=body.parent_item_id, key=request.headers.get("Idempotency-Key"))
    except (explorer.ExplorerError, InvalidCapture) as exc:
        return failure(exc)
    return Status(201 if created else 200, {"item_id": str(event.item_id), "capture_id": str(event.pk), "received_at": event.server_received_at.isoformat(), "state": "received"})


@router.delete("/explorer/folders/{folder_id}", response={200: dict, 404: dict})
def archive_folder(request, folder_id: int):
    from django.db import transaction
    with transaction.atomic():
        explorer.lock_owner(request.user.pk)
        folder = get_object_or_404(Topic, pk=folder_id, owner=request.user, archived=False)
        from .knowledge_tree import descendants
        Topic.objects.filter(pk__in=descendants(request.user.pk, folder.pk, archived=True)).update(archived=True)
    return {"state": "archived", "items_deleted": 0}
