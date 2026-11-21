"""Validated, bounded and dynamic saved queries, without membership writes."""

import unicodedata
from datetime import date, datetime, time, timedelta
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.db.models import Exists, OuterRef
from django.db.models.expressions import RawSQL
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    field_validator,
    model_validator,
)

from .api import catalog, summarize
from .models import ItemProject, ItemTag, ItemTopic, Project, Tag, Topic


class GroupCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    any: list[StrictInt] = Field(default_factory=list, max_length=100)
    all: list[StrictInt] = Field(default_factory=list, max_length=100)
    exclude: list[StrictInt] = Field(default_factory=list, max_length=100)

    @field_validator("any", "all", "exclude")
    @classmethod
    def ids(cls, value):
        if any(entry < 1 for entry in value) or len(set(value)) != len(value):
            raise ValueError("Unique positive group IDs are required")
        return value


class DateCondition(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    from_date: date | None = Field(default=None, alias="from")
    to: date | None = None

    @model_validator(mode="after")
    def ordered(self):
        if self.to == date.max:
            raise ValueError("End date is outside supported range")
        if self.from_date and self.to and self.from_date > self.to:
            raise ValueError("Start must precede end")
        return self


class CollectionQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    q: str = Field(default="", max_length=300)
    topics: GroupCondition = Field(default_factory=GroupCondition)
    projects: GroupCondition = Field(default_factory=GroupCondition)
    tags: GroupCondition = Field(default_factory=GroupCondition)
    received: DateCondition = Field(default_factory=DateCondition)
    published: DateCondition = Field(default_factory=DateCondition)
    timezone: str = "Asia/Ho_Chi_Minh"
    favorite: bool | None = Field(default=None, strict=True)
    source_fetch: Literal[
        "", "pending", "partial", "done", "failed", "not_applicable"
    ] = ""
    content_extract: Literal[
        "", "pending", "partial", "done", "failed", "not_available"
    ] = ""
    sort: Literal["saved_desc", "saved_asc", "published_desc", "title"] = "saved_desc"

    @field_validator("timezone")
    @classmethod
    def known_timezone(cls, value):
        if len(value) > 64:
            raise ValueError("Invalid timezone")
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("Invalid timezone") from None
        return value

    @field_validator("q")
    @classmethod
    def query_text(cls, value):
        if "\0" in value:
            raise ValueError("NUL is not permitted")
        return unicodedata.normalize("NFC", value.strip())


GROUPS = (
    ("topics", Topic, ItemTopic, "topic"),
    ("projects", Project, ItemProject, "project"),
    ("tags", Tag, ItemTag, "tag"),
)


def validate_groups(owner, query):
    for key, model, _, _ in GROUPS:
        condition = getattr(query, key)
        ids = set(condition.any + condition.all + condition.exclude)
        valid = model.objects.filter(owner=owner, pk__in=ids)
        if key != "tags":
            valid = valid.filter(archived=False)
        if valid.count() != len(ids):
            raise ValueError("Unknown or unavailable groups")


def matching_items(owner, query):
    """EXISTS predicates avoid join fan-out; allowlisted sort and bound values."""
    items = catalog(owner).filter(deleted_at__isnull=True)
    if query.q:
        # Use exactly the existing KT104 GIN expressions; SQL identifiers are constants.
        # q and owner are driver parameters, never SQL/DSL supplied by the client.
        sql = """
            SELECT i.id FROM catalog_item i
            WHERE i.owner_id=%s AND i.deleted_at IS NULL
              AND to_tsvector('public.kt_vi', public.kt_search_item(i.title,i.description,i.note))
                  @@ plainto_tsquery('public.kt_vi', %s)
            UNION
            SELECT d.item_id FROM processing_derivedcontent d
            JOIN catalog_item i ON i.id=d.item_id
            WHERE i.owner_id=%s AND i.deleted_at IS NULL AND d.status='active'
              AND to_tsvector('public.kt_vi', public.kt_search_text(d.text))
                  @@ plainto_tsquery('public.kt_vi', %s)
        """
        items = items.filter(pk__in=RawSQL(sql, [owner.pk, query.q, owner.pk, query.q]))
    for key, _, relation, field in GROUPS:
        condition = getattr(query, key)
        links = relation.objects.filter(
            item_id=OuterRef("pk"), **{f"{field}__owner": owner}
        )
        if key != "tags":
            links = links.filter(**{f"{field}__archived": False})
        if condition.any:
            items = items.filter(
                Exists(links.filter(**{f"{field}_id__in": condition.any}))
            )
        for value in condition.all:
            items = items.filter(Exists(links.filter(**{f"{field}_id": value})))
        if condition.exclude:
            items = items.filter(
                ~Exists(links.filter(**{f"{field}_id__in": condition.exclude}))
            )
    zone = ZoneInfo(query.timezone)
    for field, bounds in (
        ("saved_at", query.received),
        ("published_at", query.published),
    ):
        if bounds.from_date:
            items = items.filter(
                **{field + "__gte": datetime.combine(bounds.from_date, time.min, zone)}
            )
        if bounds.to:
            items = items.filter(
                **{
                    field + "__lt": datetime.combine(
                        bounds.to + timedelta(days=1), time.min, zone
                    )
                }
            )
    if query.favorite is not None:
        items = items.filter(favorite=query.favorite)
    for field in ("source_fetch", "content_extract"):
        value = getattr(query, field)
        if value:
            items = items.filter(**{field: value})
    order = {
        "saved_desc": ("-saved_at", "id"),
        "saved_asc": ("saved_at", "id"),
        "published_desc": ("-published_at", "id"),
        "title": ("title", "id"),
    }[query.sort]
    return items.order_by(*order)


def page(owner, query, offset=0, limit=50):
    items = matching_items(owner, query)
    count = items.count()
    rows = list(items[offset : offset + limit])
    return {
        "results": [summarize(item) for item in rows],
        "count": count,
        "next_offset": offset + limit if offset + limit < count else None,
    }
