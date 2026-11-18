from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import Router, Schema, Status
from ninja.security import django_auth

from catalog.models import Item

from .models import DerivedContent

router = Router(auth=django_auth, tags=["Content"])


class ContentPart(Schema):
    id: int
    kind: str
    text: str
    locator: dict
    processor: str
    processor_version: str
    truncated: bool


class ContentPage(Schema):
    results: list[ContentPart]
    next_offset: int | None


class Error(Schema):
    code: str


@router.get("/items/{item_id}/content", response={200: ContentPage, 422: Error})
def content(request, item_id: UUID, limit: int = 5, offset: int = 0):
    item = get_object_or_404(
        Item, pk=item_id, owner=request.user, deleted_at__isnull=True
    )
    if not 1 <= limit <= 20 or not 0 <= offset <= 100_000:
        return Status(422, {"code": "invalid_page"})
    parts = list(
        DerivedContent.objects.filter(
            item=item, status=DerivedContent.Status.ACTIVE
        ).order_by("asset_id", "id")[offset : offset + limit + 1]
    )
    return {
        "results": [
            {
                "id": part.pk,
                "kind": part.kind,
                "text": part.text[:50_000],
                "locator": part.source_locator,
                "processor": part.processor,
                "processor_version": part.processor_version,
                "truncated": len(part.text) > 50_000,
            }
            for part in parts[:limit]
        ],
        "next_offset": offset + limit if len(parts) > limit else None,
    }
