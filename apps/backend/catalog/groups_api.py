import unicodedata
from typing import Annotated, Literal
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from ninja import Router, Schema, Status
from ninja.security import django_auth
from pydantic import Field

from .models import (
    Assignment,
    Item,
    ItemProject,
    ItemTag,
    ItemTopic,
    Project,
    RelatedItem,
    Tag,
    Topic,
)

router = Router(tags=["Organization"], auth=django_auth)
GROUPS = {
    "topic": ("topics", Topic, ItemTopic),
    "project": ("projects", Project, ItemProject),
    "tag": ("tags", Tag, ItemTag),
}
GroupId = Annotated[int, Field(ge=1, lt=2**63)]


class Group(Schema):
    id: int
    name: str


class GroupLists(Schema):
    topics: list[Group]
    projects: list[Group]
    tags: list[Group]


class GroupCreate(Schema):
    kind: Literal["topic", "project", "tag"]
    name: str = Field(min_length=1, max_length=120)


class RelationGroup(Group):
    origin: str
    user_pinned: bool


class Organization(Schema):
    status: str
    topics: list[RelationGroup]
    projects: list[RelationGroup]
    tags: list[RelationGroup]


class OrganizationPatch(Schema):
    topic_ids: list[GroupId] | None = Field(default=None, max_length=100)
    project_ids: list[GroupId] | None = Field(default=None, max_length=100)
    tag_ids: list[GroupId] | None = Field(default=None, max_length=100)


class RelatedHit(Schema):
    item_id: UUID
    title: str
    reason: str
    relation_type: str
    confidence: float | None


class RelatedPage(Schema):
    results: list[RelatedHit]


class Error(Schema):
    code: str


def groups_for(model, owner):
    groups = model.objects.filter(owner=owner)
    return groups if model is Tag else groups.filter(archived=False)


def summarize(item):
    payload = {"status": item.classification_status}
    for field, (key, model, assignments) in GROUPS.items():
        visible = groups_for(model, item.owner).values_list("pk", flat=True)
        rows = assignments.objects.filter(item=item, **{f"{field}_id__in": visible})
        rows = rows.select_related(field).order_by(f"{field}__name", f"{field}_id")
        payload[key] = [
            {
                "id": getattr(row, f"{field}_id"),
                "name": getattr(row, field).name,
                "origin": row.origin,
                "user_pinned": row.user_pinned,
            }
            for row in rows
        ]
    return payload


@router.get("/groups", response=GroupLists)
def list_groups(request):
    return {
        key: list(
            groups_for(model, request.user).order_by("name", "id").values("id", "name")
        )
        for key, model, _ in GROUPS.values()
    }


@router.post("/groups", response={200: Group, 201: Group, 422: Error})
def create_group(request, payload: GroupCreate):
    name = unicodedata.normalize("NFC", payload.name.strip())
    try:
        valid = bool(name) and b"\x00" not in name.encode("utf-8")
    except UnicodeError:
        valid = False
    if not valid:
        return Status(422, {"code": "invalid_group_name"})
    _, model, _ = GROUPS[payload.kind]
    with transaction.atomic():
        get_user_model().objects.select_for_update().only("pk").get(pk=request.user.pk)
        matches = model.objects.filter(owner=request.user)
        if model is Topic:
            matches = matches.filter(parent__isnull=True)
        existing = next(
            (
                group
                for group in matches.order_by("id")
                if unicodedata.normalize("NFC", group.name).casefold()
                == name.casefold()
            ),
            None,
        )
        if existing:
            if model is not Tag and existing.archived:
                return Status(422, {"code": "group_archived"})
            return Status(200, existing)
        return Status(201, model.objects.create(owner=request.user, name=name))


@router.get("/items/{item_id}/organization", response=Organization)
def organization(request, item_id: UUID):
    item = get_object_or_404(Item, pk=item_id, owner=request.user)
    return summarize(item)


@router.patch("/items/{item_id}/organization", response={200: Organization, 422: Error})
def change_assignments(request, item_id: UUID, patch: OrganizationPatch):
    with transaction.atomic():
        item = get_object_or_404(
            Item.objects.select_for_update(), pk=item_id, owner=request.user
        )
        requested = {}
        for field, (_, model, assignments) in GROUPS.items():
            values = getattr(patch, f"{field}_ids")
            if values is None:
                continue
            ids = set(values)
            if groups_for(model, request.user).filter(pk__in=ids).count() != len(ids):
                return Status(422, {"code": "unknown_group"})
            requested[field] = (assignments, ids)

        for field, (assignments, ids) in requested.items():
            id_field = f"{field}_id"
            rows = assignments.objects.filter(item=item)
            rows.filter(Q(origin=Assignment.Origin.USER) | Q(user_pinned=True)).exclude(
                **{f"{id_field}__in": ids}
            ).delete()
            for group_id in sorted(ids):
                assignments.objects.update_or_create(
                    item=item,
                    **{id_field: group_id},
                    defaults={
                        "origin": Assignment.Origin.USER,
                        "user_pinned": True,
                        "confidence": None,
                        "method_version": "",
                        "source_version": "",
                    },
                )
        return summarize(item)


@router.get("/items/{item_id}/related", response=RelatedPage)
def related(request, item_id: UUID):
    item = get_object_or_404(
        Item, pk=item_id, owner=request.user, deleted_at__isnull=True
    )
    links = (
        RelatedItem.objects.filter(
            Q(item_a=item) | Q(item_b=item),
            status=RelatedItem.Status.ACTIVE,
            item_a__owner=request.user,
            item_b__owner=request.user,
            item_a__deleted_at__isnull=True,
            item_b__deleted_at__isnull=True,
        )
        .select_related("item_a", "item_b")
        .order_by(F("confidence").desc(nulls_last=True), "id")[:30]
    )
    results = []
    for relation in links:
        peer = relation.item_b if relation.item_a_id == item.pk else relation.item_a
        results.append(
            {
                "item_id": peer.pk,
                "title": peer.title,
                "reason": relation.reason,
                "relation_type": relation.relation_type,
                "confidence": relation.confidence,
            }
        )
    return {"results": results}
