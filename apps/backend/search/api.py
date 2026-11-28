import math
from dataclasses import asdict
from uuid import UUID

from ninja import Router, Schema, Status
from ninja.security import django_auth

from catalog.models import Item

from .quote_reader import QuoteCheck, Verification
from .services import MAX_PAGE_SIZE, SearchCursor, SearchFilters, SearchService

router = Router(tags=["Search"], auth=django_auth)


class Evidence(Schema):
    source: str
    snippet: str
    locator: dict | None
    provenance: dict


class Hit(Schema):
    item_id: UUID
    title: str
    score: float
    evidence: list[Evidence]
    verification: Verification | None = None


class Cursor(Schema):
    score: float
    item_id: UUID


class Page(Schema):
    results: list[Hit]
    next_cursor: Cursor | None
    match_kind: str = "standard"
    can_expand: bool = False
    ranking: str = "lexical"
    quote_check: QuoteCheck | None = None


class Error(Schema):
    code: str


def browse_groups(owner, group_filters, cursor, limit, exclude_item_id=None):
    if not group_filters:
        return {"results": [], "next_cursor": None}
    queryset = Item.objects.filter(
        owner=owner, deleted_at__isnull=True, **group_filters
    )
    if exclude_item_id is not None:
        queryset = queryset.exclude(pk=exclude_item_id)
    if cursor:
        if cursor.score != 0:
            raise ValueError("group cursors must have a zero score")
        queryset = queryset.filter(pk__gt=cursor.item_id)
    items = list(queryset.order_by("id").values("id", "title")[: limit + 1])
    return {
        "results": [
            {"item_id": item["id"], "title": item["title"], "score": 0, "evidence": []}
            for item in items[:limit]
        ],
        "next_cursor": {"score": 0, "item_id": items[limit - 1]["id"]}
        if len(items) > limit
        else None,
    }


@router.get("/search", response={200: Page, 422: Error}, exclude_unset=True)
def search(
    request,
    q: str = "",
    topic_id: int | None = None,
    project_id: int | None = None,
    tag_id: int | None = None,
    cursor_score: float | None = None,
    cursor_item_id: UUID | None = None,
    limit: int = 20,
    expand: bool = False,
    exclude_item_id: UUID | None = None,
):
    if (
        (cursor_score is None) != (cursor_item_id is None)
        or (cursor_score is not None and not math.isfinite(cursor_score))
        or not 1 <= limit <= MAX_PAGE_SIZE
        or any(
            value is not None and not 1 <= value < 2**63
            for value in (topic_id, project_id, tag_id)
        )
    ):
        return Status(422, {"code": "invalid_search"})
    cursor = (
        SearchCursor(cursor_score, cursor_item_id)
        if cursor_item_id is not None
        else None
    )
    try:
        q.encode("utf-8")
        if not q.strip():
            group_filters = {
                field: value
                for field, value in (
                    ("itemtopic__topic_id", topic_id),
                    ("itemproject__project_id", project_id),
                    ("itemtag__tag_id", tag_id),
                )
                if value is not None
            }
            return {"match_kind": "standard", "can_expand": False, "ranking": "lexical",
                    **browse_groups(request.user, group_filters, cursor, limit, exclude_item_id)}
        page = SearchService().search(
            SearchFilters(request.user.pk, topic_id, project_id, tag_id, exclude_item_id),
            q,
            cursor,
            limit=limit,
            expand=expand,
        )
        results = []
        for hit in page.hits:
            row = asdict(hit)
            if hit.verification is None:
                del row["verification"]
            results.append(row)
        return {
            "results": results,
            "next_cursor": asdict(page.next_cursor) if page.next_cursor else None,
            "match_kind": page.match_kind,
            "can_expand": page.can_expand,
            "ranking": page.ranking,
            **({"quote_check": asdict(page.quote_check)} if page.quote_check is not None else {}),
        }
    except (ValueError, UnicodeError):
        return Status(422, {"code": "invalid_search"})
