from datetime import datetime
from uuid import UUID

from django.db import transaction
from django.db.models import (
    Case,
    Exists,
    IntegerField,
    OuterRef,
    Prefetch,
    Q,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Substr
from django.shortcuts import get_object_or_404
from django.utils import timezone
from jobs.repository import JobRepository
from ninja import Router, Schema, Status
from ninja.security import django_auth
from processing.models import DerivedContent
from pydantic import Field
from storage.drive import DriveError
from storage.models import Asset, StorageLocation
from storage.service import DRIVE_PROVIDER, storage_for_owner

from .models import Item, ItemProject, ItemTag, ItemTopic, Source

router = Router(tags=["Library"], auth=django_auth)


class AssetSummary(Schema):
    asset_id: UUID
    filename: str
    status: str
    mime: str


class ItemSummary(Schema):
    item_id: UUID
    kind: str
    title: str
    description: str
    note: str
    user_edit_version: int
    saved_at: datetime
    published_at: datetime | None
    updated_at: datetime
    favorite: bool
    deleted: bool
    classification_status: str
    original_url: str
    source_fetch: str
    asset_storage: str
    content_extract: str
    assets: list[AssetSummary]
    knowledge_excerpt: str = ""


class ItemPage(Schema):
    results: list[ItemSummary]
    next_offset: int | None


class ItemPatch(Schema):
    expected_edit_version: int | None = Field(default=None, ge=0, strict=True)
    title: str | None = Field(default=None, max_length=512)
    description: str | None = Field(default=None, max_length=20_000)
    note: str | None = Field(default=None, max_length=100_000)
    favorite: bool | None = None
    deleted: bool | None = None


class ViewLink(Schema):
    url: str


class Error(Schema):
    code: str


def catalog(owner):
    assets = Asset.objects.order_by("id").prefetch_related(
        Prefetch(
            "locations",
            queryset=StorageLocation.objects.filter(provider=DRIVE_PROVIDER),
            to_attr="drive_locations",
        )
    )
    excerpt = (
        DerivedContent.objects.filter(item_id=OuterRef("pk"), status="active")
        .annotate(
            read_priority=Case(
                When(
                    kind__in=[
                        "transcript",
                        "video_transcript",
                        "subtitle",
                        "subtitles",
                        "caption",
                        "captions",
                    ],
                    then=Value(0),
                ),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by("read_priority", "created_at", "id")
        .values("text")[:1]
    )
    return (
        Item.objects.filter(owner=owner)
        .annotate(
            extracted_excerpt=Substr(Subquery(excerpt), 1, 512),
            has_user_groups=Exists(
                ItemTopic.objects.filter(
                    item_id=OuterRef("pk"), topic__owner=owner, topic__archived=False
                ).filter(Q(origin="user") | Q(user_pinned=True))
            )
            | Exists(
                ItemProject.objects.filter(
                    item_id=OuterRef("pk"),
                    project__owner=owner,
                    project__archived=False,
                ).filter(Q(origin="user") | Q(user_pinned=True))
            )
            | Exists(
                ItemTag.objects.filter(item_id=OuterRef("pk"), tag__owner=owner).filter(
                    Q(origin="user") | Q(user_pinned=True)
                )
            ),
        )
        .prefetch_related(
            Prefetch(
                "sources",
                queryset=Source.objects.order_by("id"),
                to_attr="ordered_sources",
            ),
            Prefetch("assets", queryset=assets, to_attr="ordered_assets"),
        )
    )


def summarize(item):
    original_url = item.ordered_sources[0].original_url if item.ordered_sources else ""
    note_only = (
        item.kind == Item.Kind.TEXT
        and not item.ordered_sources
        and not item.ordered_assets
    )
    return {
        "item_id": item.pk,
        "kind": item.kind,
        "title": item.title,
        "description": item.description,
        "note": item.note,
        "knowledge_excerpt": item.note[:512] or item.extracted_excerpt or "",
        "saved_at": item.saved_at,
        "published_at": item.published_at,
        "updated_at": item.updated_at,
        "user_edit_version": item.user_edit_version,
        "favorite": item.favorite,
        "deleted": item.deleted_at is not None,
        "classification_status": "user_assigned"
        if item.has_user_groups
        else item.classification_status,
        "original_url": original_url,
        "source_fetch": "not_applicable" if note_only else item.source_fetch,
        "asset_storage": "not_applicable" if note_only else item.asset_storage,
        "content_extract": "not_available" if note_only else item.content_extract,
        "assets": [
            {
                "asset_id": asset.pk,
                "filename": asset.original_filename,
                "status": asset.drive_locations[0].status
                if asset.drive_locations
                else "pending",
                "mime": asset.mime,
            }
            for asset in item.ordered_assets
        ],
    }


@router.get("/items", response={200: ItemPage, 422: Error})
def list_items(
    request,
    limit: int = 50,
    offset: int = 0,
    deleted: bool = False,
    favorite: bool = False,
    unclassified: bool = False,
    node_id: int | None = None,
    unfiled: bool = False,
):
    if not 1 <= limit <= 100 or not 0 <= offset <= 1_000_000:
        return Status(422, {"code": "invalid_page"})
    items = catalog(request.user).filter(deleted_at__isnull=not deleted)
    if node_id is not None or unfiled:
        from .knowledge_tree import tree

        nodes = tree(request.user.pk)
        visible = {row["id"] for row in nodes}
        if node_id is not None:
            if node_id not in visible:
                from django.http import Http404

                raise Http404
            ids = [row["id"] for row in nodes if node_id in row["path_ids"]]
            items = items.filter(itemtopic__topic_id__in=ids).distinct()
        elif unfiled:
            # An unfiled Item has no active folder assignment or primary home.
            # A structural note parent is not a folder; inactive/archived
            # memberships do not hide a note from this virtual collection.
            from .explorer import without_visible_folder

            items = without_visible_folder(items, request.user.pk)
    if favorite:
        items = items.filter(favorite=True)
    if unclassified:
        items = items.filter(
            itemtopic__isnull=True, itemproject__isnull=True, itemtag__isnull=True
        )
    page = list(items.order_by("-saved_at", "id")[offset : offset + limit + 1])
    return {
        "results": [summarize(item) for item in page[:limit]],
        "next_offset": offset + limit if len(page) > limit else None,
    }


@router.get("/items/{item_id}", response=ItemSummary)
def get_item(request, item_id: UUID):
    return summarize(get_object_or_404(catalog(request.user), pk=item_id))


@router.patch("/items/{item_id}", response={200: ItemSummary, 409: Error, 422: Error})
def edit_item(request, item_id: UUID, patch: ItemPatch):
    changes = patch.model_dump(exclude_none=True)
    expected_version = changes.pop("expected_edit_version", None)
    try:
        text_contains_nul = any(
            b"\x00" in value.encode("utf-8")
            for value in changes.values()
            if isinstance(value, str)
        )
    except UnicodeError:
        return Status(422, {"code": "invalid_text"})
    if text_contains_nul:
        return Status(422, {"code": "invalid_text"})

    with transaction.atomic():
        item = get_object_or_404(
            Item.objects.select_for_update(), pk=item_id, owner=request.user
        )
        if expected_version is not None and (
            expected_version != item.user_edit_version
            or (item.deleted_at and changes.keys() & {"title", "description", "note"})
        ):
            return Status(409, {"code": "edit_conflict"})
        if "deleted" in changes:
            remove = changes.pop("deleted")
            changes["deleted_at"] = (
                (item.deleted_at or timezone.now()) if remove else None
            )
        changed = {
            key: value for key, value in changes.items() if getattr(item, key) != value
        }
        if changed.keys() & {"title", "description", "note"}:
            changed["user_edit_version"] = item.user_edit_version + 1
        if changed:
            for key, value in changed.items():
                setattr(item, key, value)
            item.save(update_fields=[*changed, "updated_at"])
            if changed.keys() & {"title", "description", "note", "deleted_at"}:
                JobRepository.enqueue(
                    kind="organize",
                    idempotency_key=f"item:{item.pk}:edit:{item.user_edit_version}:deleted:{item.deleted_at}",
                    item=item,
                    input_ref={"item_id": str(item.pk)},
                )
    return summarize(catalog(request.user).get(pk=item_id))


@router.get("/assets/{asset_id}/open", response={200: ViewLink, 409: Error, 503: Error})
def view_asset(request, asset_id: UUID):
    asset = get_object_or_404(
        Asset.objects.select_related("item"),
        pk=asset_id,
        item__owner=request.user,
        item__deleted_at__isnull=True,
    )
    try:
        return {"url": storage_for_owner(request.user.pk).open(asset)}
    except DriveError as error:
        status = 503 if error.retryable else 409
        return Status(status, {"code": error.code})
