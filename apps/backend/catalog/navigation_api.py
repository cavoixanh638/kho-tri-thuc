"""Owner-scoped navigation and explicit note references, without inferred edges."""

import unicodedata
from typing import Literal
from uuid import UUID

from django.db.models import Q
from django.db.models.functions import Substr
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.security import django_auth

from .groups_api import _backlinks, _inline_item_links
from .models import Item, Topic

router = Router(auth=django_auth, tags=["Knowledge navigation"])


def label(item):
    text = item.title or (item.preview if hasattr(item, "preview") else item.note[:120])
    lines = text.lstrip("# \r\n\t").splitlines()
    return lines[0][:120] if lines else "Chưa đặt tên"


def hit(item):
    return {
        "item_id": str(item.pk),
        "title": label(item),
        "saved_at": item.saved_at.isoformat(),
    }


@router.get("/navigation")
def navigation(
    request,
    q: str = "",
    kind: Literal["all", "items", "folders"] = "all",
    offset: int = 0,
):
    if len(q) > 200 or "\0" in q or not 0 <= offset <= 100_000:
        return JsonResponse({"code": "invalid_navigation_query"}, status=422)
    query = unicodedata.normalize("NFC", q.strip())[:200]
    rows = Item.objects.filter(owner=request.user, deleted_at__isnull=True)
    if query:
        rows = rows.filter(
            Q(title__icontains=query) | Q(title="", note__icontains=query)
        )
    items = (
        list(
            rows.annotate(preview=Substr("note", 1, 120))
            .only("id", "title", "saved_at")
            .order_by("-saved_at", "id")[offset : offset + 21]
        )
        if kind != "folders"
        else []
    )
    folders = Topic.objects.filter(owner=request.user, archived=False)
    if query:
        folders = folders.filter(name__icontains=query)
    folders = (
        list(folders.only("id", "name", "parent_id").order_by("name", "id")[:20])
        if kind != "items"
        else []
    )
    return {
        "items": [hit(item) for item in items[:20]],
        "folders": [
            {"id": row.pk, "name": row.name, "parent_id": row.parent_id}
            for row in folders
        ],
        "next_offset": offset + 20 if len(items) > 20 else None,
    }


@router.get("/items/{item_id}/links")
def note_links(request, item_id: UUID):
    item = get_object_or_404(
        Item, pk=item_id, owner=request.user, deleted_at__isnull=True
    )
    visible = Item.objects.filter(owner=request.user, deleted_at__isnull=True)
    targets = _inline_item_links(item.note)
    outgoing = (
        visible.filter(pk__in=targets)
        .exclude(pk=item.pk)
        .only("id", "title", "note", "saved_at")
        .order_by("title", "id")
    )
    incoming, incoming_count = _backlinks(item)
    # A mention is a bounded, explicitly labelled lexical candidate. It never
    # inserts a backlink, RelatedItem or structural relation.
    mentions, truncated = [], False
    title = unicodedata.normalize("NFC", item.title.strip())
    if len(title) >= 3:
        candidates = (
            visible.exclude(pk=item.pk)
            .filter(note__icontains=title)
            .only("id", "title", "note", "saved_at")
            .order_by("title", "id")
        )
        for peer in candidates[:201]:
            if item.pk not in _inline_item_links(peer.note):
                if len(mentions) == 30:
                    truncated = True
                    break
                mentions.append(hit(peer))
    rows = list(outgoing[:31])
    return {
        "outgoing": [hit(peer) for peer in rows[:30]],
        "incoming": incoming,
        "unlinked": mentions,
        "counts": {
            "outgoing": outgoing.count(),
            "incoming": incoming_count,
            "unlinked_shown": len(mentions),
        },
        "truncated": len(rows) > 30 or truncated,
        "scope": "explicit_inline_markdown; mentions_are_candidates_only",
    }
