import math
import re
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
    path: str = ""


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
    method_version: str
    source_version: str


class ExplicitHit(Schema):
    item_id: UUID
    title: str
    source_version: str


class SameGroupHit(Schema):
    item_id: UUID
    title: str
    groups: list[dict]


class RelatedPage(Schema):
    results: list[RelatedHit]
    backlinks: list[ExplicitHit]
    same_group: list[SameGroupHit]
    counts: dict[str, int]
    backlinks_scope: str
    evidence: dict


class Error(Schema):
    code: str


def groups_for(model, owner):
    groups = model.objects.filter(owner=owner)
    return groups if model is Tag else groups.filter(archived=False)


def summarize(item):
    from .knowledge_tree import tree

    payload = {"status": item.classification_status}
    topic_paths = {row["id"]: row["path"] for row in tree(item.owner_id)}
    for field, (key, model, assignments) in GROUPS.items():
        visible = groups_for(model, item.owner).values_list("pk", flat=True)
        rows = assignments.objects.filter(item=item, **{f"{field}_id__in": visible})
        rows = rows.select_related(field).order_by(f"{field}__name", f"{field}_id")
        payload[key] = [
            {
                "id": getattr(row, f"{field}_id"),
                "name": getattr(row, field).name,
                "path": topic_paths.get(getattr(row, field).pk, "")
                if field == "topic"
                else "",
                "origin": row.origin,
                "user_pinned": row.user_pinned,
            }
            for row in rows
        ]
    return payload


@router.get("/groups", response=GroupLists)
def list_groups(request):
    from .knowledge_tree import tree

    payload = {
        key: list(
            groups_for(model, request.user).order_by("name", "id").values("id", "name")
        )
        for key, model, _ in GROUPS.values()
    }
    payload["topics"] = [
        {"id": row["id"], "name": row["name"], "path": row["path"]}
        for row in tree(request.user.pk)
    ]
    return payload


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
        .order_by(F("confidence").desc(nulls_last=True), "id")
    )
    results = []
    for relation in links[:30]:
        peer = relation.item_b if relation.item_a_id == item.pk else relation.item_a
        results.append(
            {
                "item_id": peer.pk,
                "title": peer.title,
                "reason": relation.reason,
                "relation_type": relation.relation_type,
                "confidence": relation.confidence,
                "method_version": relation.method_version,
                "source_version": relation.source_version,
            }
        )
    backlinks, backlink_count = _backlinks(item)
    same_group, group_count = _same_group(item)
    return {
        "results": results,
        "backlinks": backlinks,
        "same_group": same_group,
        "counts": {
            "related": links.count(),
            "backlinks": backlink_count,
            "same_group": group_count,
        },
        "backlinks_scope": "inline_markdown_only",
        "evidence": _source_evidence(item),
    }


def _inline_item_links(markdown):
    """Conservative inline Markdown adapter, not a complete Markdown parser.

    Only authored [label](#/muc/UUID) destinations count. References, HTML,
    images, plain URLs, code and derived lexical matches are not backlinks.
    Unsupported constructs may be omitted; they must not create false links.
    """
    lines, fence, html = [], None, False
    for line in markdown.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                fence = None
            continue
        if marker:
            fence = marker[1]
            continue
        if not line.strip():
            html = False
        if re.search(r"</?[A-Za-z!]", line):
            html = True
        if (
            html
            or "![" in line
            or line.startswith(("    ", "\t"))
            or line.lstrip().startswith(">")
        ):
            continue
        lines.append(line)
    text = "\n".join(lines)
    # Inline backtick runs can cross line boundaries. Mask an unmatched run's
    # remainder too: conservative omission is safer than treating code as a link.
    cursor, plain = 0, []
    for opening in re.finditer(r"`+", text):
        if opening.start() < cursor:
            continue
        plain.append(text[cursor : opening.start()])
        plain.append(" ")
        closing = re.search(r"(?<!`)" + opening[0] + r"(?!`)", text[opening.end() :])
        cursor = len(text) if closing is None else opening.end() + closing.end()
    plain.append(text[cursor:])
    text = "".join(plain)
    pattern = r"(?<![\\!])\[[^\]<>\\\n]*\]\(\s*(<)?#/muc/([a-fA-F0-9-]{36})(?(1)>)\s*\)"
    ids = set()
    for match in re.finditer(pattern, text):
        try:
            ids.add(UUID(match[2]))
        except ValueError:
            pass
    return ids


def _backlinks(item):
    peers = (
        Item.objects.filter(
            owner_id=item.owner_id,
            deleted_at__isnull=True,
            note__icontains=f"#/muc/{item.pk}",
        )
        .exclude(pk=item.pk)
        .only("id", "title", "note", "user_edit_version")
    )
    hits, count = [], 0
    for peer in peers.order_by("title", "id").iterator(chunk_size=100):
        if item.pk in _inline_item_links(peer.note):
            count += 1
            if len(hits) < 30:
                hits.append(
                    {
                        "item_id": peer.pk,
                        "title": peer.title,
                        "source_version": f"note-edit:{peer.user_edit_version}",
                    }
                )
    return hits, count


def _same_group(item):
    peers = {}
    for kind, (_, model, assignments) in GROUPS.items():
        visible = groups_for(model, item.owner)
        ids = assignments.objects.filter(
            item=item, **{f"{kind}__in": visible}
        ).values_list(f"{kind}_id", flat=True)
        rows = (
            assignments.objects.filter(
                item__owner_id=item.owner_id,
                item__deleted_at__isnull=True,
                **{f"{kind}_id__in": ids},
            )
            .exclude(item=item)
            .select_related("item", kind)
            .order_by("item__title", "item_id")
        )
        for row in rows:
            peer = peers.setdefault(
                row.item_id,
                {"item_id": row.item_id, "title": row.item.title, "groups": []},
            )
            group = getattr(row, kind)
            peer["groups"].append({"kind": kind, "id": group.pk, "name": group.name})
    ordered = sorted(
        peers.values(), key=lambda peer: (peer["title"], str(peer["item_id"]))
    )
    return ordered[:30], len(ordered)


def _safe_locator(raw, current_asset):
    if not isinstance(raw, dict) or current_asset is False:
        return {}
    locator = {}
    page = raw.get("page")
    if type(page) is int and 1 <= page <= 1_000_000:
        locator["page"] = page
    start, end = raw.get("start_seconds"), raw.get("end_seconds")
    if type(start) in (int, float) and math.isfinite(start) and 0 <= start <= 10**8:
        locator["start_seconds"] = start
        if type(end) in (int, float) and math.isfinite(end) and start <= end <= 10**8:
            locator["end_seconds"] = end
    return locator


def _source_evidence(item):
    from processing.models import DerivedContent
    from storage.models import StorageLocation

    source_rows = list(item.sources.order_by("id")[:101])
    asset_rows = list(item.assets.order_by("id").prefetch_related("locations")[:101])
    sources = {
        source.pk: {
            "source_id": source.pk,
            "original_url": source.original_url,
            "asset_ids": [],
            "parts": [],
        }
        for source in source_rows[:100]
    }
    assets = {}
    for asset in asset_rows[:100]:
        drive = next(
            (
                location
                for location in asset.locations.all()
                if location.provider == "google_drive"
            ),
            None,
        )
        assets[str(asset.pk)] = {
            "asset_id": str(asset.pk),
            "filename": asset.original_filename,
            "mime": asset.mime,
            "content_version": asset.content_version,
            "status": drive.status if drive else StorageLocation.Status.PENDING,
            "parts": [],
            "sha256": asset.sha256,
        }
    parts = list(DerivedContent.objects.filter(item=item).order_by("id")[:1001])
    unassociated = []
    for part in parts[:1000]:
        raw = part.source_locator if isinstance(part.source_locator, dict) else {}
        source_id = raw.get("source_id")
        source_id = (
            source_id if type(source_id) is int and source_id in sources else None
        )
        asset = assets.get(str(part.asset_id)) if part.asset_id else None
        # A corrupt/cross-item FK must not leak file metadata or imply association.
        current = (
            bool(asset["sha256"] and part.input_hash == asset["sha256"])
            if asset
            else None
        )
        evidence = {
            "id": part.pk,
            "kind": part.kind,
            "status": part.status,
            "processor": part.processor,
            "processor_version": part.processor_version,
            "input_hash": part.input_hash,
            "has_text": bool(part.text.strip()),
            "asset_id": asset["asset_id"] if asset else None,
            "source_id": source_id,
            "matches_current_asset": current,
            "locator": _safe_locator(raw, current) if part.status == "active" else {},
        }
        if asset:
            asset["parts"].append(evidence)
            if source_id and asset["asset_id"] not in sources[source_id]["asset_ids"]:
                sources[source_id]["asset_ids"].append(asset["asset_id"])
        elif source_id and not part.asset_id:
            sources[source_id]["parts"].append(evidence)
        else:
            # Unknown source/asset association stays explicit rather than guessed.
            evidence["locator"] = {}
            unassociated.append(evidence)
    for asset in assets.values():
        asset.pop("sha256")
    return {
        "sources": list(sources.values()),
        "assets": list(assets.values()),
        "unassociated_parts": unassociated,
        "truncated": len(source_rows) > 100
        or len(asset_rows) > 100
        or len(parts) > 1000,
    }
