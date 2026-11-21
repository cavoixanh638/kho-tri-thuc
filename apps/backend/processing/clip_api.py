from typing import Literal
from uuid import UUID

from catalog.models import Item
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from ninja import Router, Schema, Status
from ninja.security import django_auth
from pydantic import Field

from . import clips
from .models import ClipAnnotation, DerivedContent

router = Router(auth=django_auth, tags=["Source clips"])


class Preview(Schema):
    mode: Literal["link", "article", "selection"]
    url: str = Field(default="", max_length=4096)
    quote: str = Field(default="", max_length=60_000)
    target_item_id: UUID | None = None
    derived_id: int | None = Field(default=None, ge=1, strict=True)
    start: int | None = Field(default=None, ge=0, strict=True)
    end: int | None = Field(default=None, ge=0, strict=True)


class Submit(Schema):
    receipt: str = Field(max_length=300_000)


class Insert(Schema):
    expected_edit_version: int = Field(ge=0, strict=True)


def failure(exc):
    code = str(exc)
    return Status(
        409
        if "conflict" in code or "changed" in code or "idempotency" in code
        else 422,
        {"code": code},
    )


@router.post("/clips/preview", response={200: dict, 409: dict, 422: dict})
def preview(request, body: Preview):
    try:
        return clips.preview(request.user, body)
    except clips.ClipError as exc:
        return failure(exc)


@router.post("/clips", response={200: dict, 201: dict, 409: dict, 422: dict})
def submit(request, body: Submit):
    from ingestion.services import InvalidCapture

    try:
        result = clips.submit(
            request.user, body.receipt, request.headers.get("Idempotency-Key")
        )
        return Status(201 if result["created"] else 200, result)
    except (clips.ClipError, InvalidCapture) as exc:
        return failure(exc)


@router.get("/items/{item_id}/clips")
def list_clips(request, item_id: UUID, offset: int = 0):
    if not 0 <= offset <= 100_000:
        return JsonResponse({"code": "invalid_offset"}, status=422)
    item = get_object_or_404(
        Item, pk=item_id, owner=request.user, deleted_at__isnull=True
    )
    rows = list(
        ClipAnnotation.objects.filter(item=item)
        .select_related("item", "part__item", "part__asset", "asset")
        .order_by("-created_at", "pk")[offset : offset + 21]
    )
    return {
        "results": [clips.summary(row) for row in rows[:20]],
        "next_offset": offset + 20 if len(rows) > 20 else None,
    }


@router.get("/clips/{annotation_id}/source", response={200: dict, 409: dict})
def source_excerpt(request, annotation_id: UUID):
    row = get_object_or_404(
        ClipAnnotation.objects.select_related("item", "part__item", "part__asset"),
        pk=annotation_id,
        item__owner=request.user,
        item__deleted_at__isnull=True,
    )
    current = clips.state(row)
    if current != "current":
        return Status(409, {"code": "quote_source_changed", "state": current})
    start, end = row.locator["text_start"], row.locator["text_end"]
    return {
        "before": row.part.text[max(0, start - 500) : start],
        "quote": row.quote,
        "after": row.part.text[end : end + 500],
        "locator": row.locator,
        "source_version": row.source_version,
        "state": current,
    }


@router.get("/items/{item_id}/clip-sources")
def clip_sources(request, item_id: UUID, offset: int = 0):
    if not 0 <= offset <= 100_000:
        return JsonResponse({"code": "invalid_offset"}, status=422)
    item = get_object_or_404(
        Item, pk=item_id, owner=request.user, deleted_at__isnull=True
    )
    rows = list(
        DerivedContent.objects.filter(item=item, status="active")
        .select_related("asset")
        .order_by("pk")[offset : offset + 21]
    )
    return {
        "results": [
            {
                "id": row.pk,
                "kind": row.kind,
                "text": row.text[:60_000],
                "processor_version": row.processor_version,
                "source_version": row.input_hash,
                "locator": row.source_locator,
                "asset_id": str(row.asset_id) if row.asset_id else None,
            }
            for row in rows[:20]
            if not row.asset_id or row.asset.item_id == item.pk
        ],
        "next_offset": offset + 20 if len(rows) > 20 else None,
    }


@router.post(
    "/clips/{annotation_id}/insert", response={200: dict, 409: dict, 422: dict}
)
def insert(request, annotation_id: UUID, body: Insert):
    try:
        return clips.insert(request.user, annotation_id, body.expected_edit_version)
    except clips.ClipError as exc:
        return failure(exc)
