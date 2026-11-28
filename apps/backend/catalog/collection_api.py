"""Saved smart collections: query definitions, not physical folders."""

import unicodedata
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from ninja import Router, Schema, Status
from pydantic import ValidationError
from ninja.security import django_auth
from pydantic import Field

from .collection_models import SavedCollection
from .collection_service import CollectionQuery, page, validate_groups

router = Router(auth=django_auth, tags=["Smart collections"])


class Definition(Schema):
    name: str = Field(min_length=1, max_length=120)
    query: CollectionQuery = Field(default_factory=CollectionQuery)
    view: str = Field(default="list", pattern="^(list|table|card|timeline)$")


class Update(Definition):
    expected_version: int = Field(ge=1, strict=True)


class Preview(Schema):
    query: CollectionQuery
    offset: int = Field(default=0, ge=0, le=1_000_000)
    limit: int = Field(default=50, ge=1, le=100)


def summary(value):
    return {
        "id": str(value.pk),
        "name": value.name,
        "query": value.query,
        "view": value.view,
        "version": value.version,
        "created_at": value.created_at.isoformat(),
        "updated_at": value.updated_at.isoformat(),
    }


def prepare(owner, body):
    name = unicodedata.normalize("NFC", body.name.strip())
    if not name or any(ord(character) < 32 for character in name):
        raise ValueError("Invalid collection name")
    validate_groups(owner, body.query)
    return {
        "name": name,
        "normalized_name": name.casefold(),
        "query": body.query.model_dump(mode="json", by_alias=True),
        "view": body.view,
    }


@router.get("/collections")
def collections(request):
    return {
        "results": [
            summary(value)
            for value in SavedCollection.objects.filter(owner=request.user).order_by(
                "name", "id"
            )[:100]
        ]
    }


@router.post("/collections", response={201: dict, 409: dict, 422: dict})
def create(request, body: Definition):
    try:
        values = prepare(request.user, body)
        with transaction.atomic():
            # Serialize per owner, bounding both UI list and definition count.
            get_user_model().objects.select_for_update().get(pk=request.user.pk)
            if SavedCollection.objects.filter(owner=request.user).count() >= 100:
                return Status(422, {"code": "collection_limit"})
            value = SavedCollection.objects.create(owner=request.user, **values)
        return Status(201, summary(value))
    except ValueError:
        return Status(422, {"code": "collection_invalid"})
    except IntegrityError:
        return Status(409, {"code": "collection_name_conflict"})


@router.post("/collections/preview", response={200: dict, 422: dict})
def preview(request, body: Preview):
    try:
        validate_groups(request.user, body.query)
        return page(request.user, body.query, body.offset, body.limit)
    except ValueError:
        return Status(422, {"code": "collection_invalid"})


@router.get("/collections/{collection_id}")
def read(request, collection_id: UUID):
    return summary(
        get_object_or_404(SavedCollection, pk=collection_id, owner=request.user)
    )


@router.patch(
    "/collections/{collection_id}", response={200: dict, 409: dict, 422: dict}
)
def update(request, collection_id: UUID, body: Update):
    try:
        values = prepare(request.user, body)
        with transaction.atomic():
            value = get_object_or_404(
                SavedCollection.objects.select_for_update(),
                pk=collection_id,
                owner=request.user,
            )
            if value.version != body.expected_version:
                return Status(409, {"code": "collection_version_conflict"})
            for key, entry in values.items():
                setattr(value, key, entry)
            value.version += 1
            value.save()
        return summary(value)
    except ValueError:
        return Status(422, {"code": "collection_invalid"})
    except IntegrityError:
        return Status(409, {"code": "collection_name_conflict"})


@router.delete("/collections/{collection_id}")
def delete(request, collection_id: UUID):
    value = get_object_or_404(SavedCollection, pk=collection_id, owner=request.user)
    value.delete()
    return {"state": "deleted"}


@router.get("/collections/{collection_id}/items", response={200: dict, 422: dict})
def results(request, collection_id: UUID, offset: int = 0, limit: int = 50):
    value = get_object_or_404(SavedCollection, pk=collection_id, owner=request.user)
    if not 0 <= offset <= 1_000_000 or not 1 <= limit <= 100:
        return Status(422, {"code": "collection_page_invalid"})
    try:
        query = CollectionQuery.model_validate(value.query)
    except (ValidationError, ValueError, TypeError):
        # Keep legacy definitions available to edit, but fail closed on query.
        return Status(422, {"code": "collection_definition_invalid"})
    return page(request.user, query, offset, limit)
