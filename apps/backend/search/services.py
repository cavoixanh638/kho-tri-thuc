import json
import math
import unicodedata
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from django.db import connection

from .queries import SEARCH_SQL


CAPTURE_SCAN_LIMIT = 1000
MAX_QUERY_LENGTH = 300
MAX_PAGE_SIZE = 100


@dataclass(frozen=True)
class SearchFilters:
    owner_id: int
    topic_id: int | None = None
    project_id: int | None = None
    tag_id: int | None = None
    exclude_item_id: UUID | None = None


@dataclass(frozen=True)
class SearchCursor:
    score: float
    item_id: UUID


@dataclass(frozen=True)
class SearchEvidence:
    source: Literal["item", "derived_content", "capture_event"]
    snippet: str
    locator: dict | None
    provenance: dict


@dataclass(frozen=True)
class SearchHit:
    item_id: UUID
    title: str
    score: float
    evidence: tuple[SearchEvidence, ...]


@dataclass(frozen=True)
class SearchPage:
    hits: tuple[SearchHit, ...] = ()
    next_cursor: SearchCursor | None = None


class SearchService:
    def search(
        self,
        filters: SearchFilters,
        query: str,
        cursor: SearchCursor | None = None,
        *,
        limit: int = 20,
    ) -> SearchPage:
        """Return visible items in rank order with the best match per source.

        The history branch searches up to the latest 1,000 link annotations in
        scope. Reuse a cursor with the same query and filters on the next page.
        """
        if not 1 <= limit <= MAX_PAGE_SIZE:
            raise ValueError(f"limit must be between 1 and {MAX_PAGE_SIZE}")
        if cursor is not None and not math.isfinite(cursor.score):
            raise ValueError("cursor score must be finite")
        query = " ".join(unicodedata.normalize("NFC", query).split())
        if len(query) > MAX_QUERY_LENGTH or "\0" in query:
            raise ValueError(f"query must be at most {MAX_QUERY_LENGTH} characters without NUL")
        if not any(character.isalnum() for character in query):
            return SearchPage()

        with connection.cursor() as db_cursor:
            db_cursor.execute(SEARCH_SQL, _search_params(filters, query, cursor, limit))
            rows = db_cursor.fetchall()

        summaries = {}
        for item_id, title, score, source, snippet, locator, provenance in rows:
            if item_id not in summaries:
                summaries[item_id] = (title, score, [])
            summaries[item_id][2].append(SearchEvidence(
                source=source,
                snippet=snippet,
                locator=json.loads(locator) if locator is not None else None,
                provenance=json.loads(provenance),
            ))
        hits = tuple(
            SearchHit(item_id, title, score, tuple(evidence))
            for item_id, (title, score, evidence) in summaries.items()
        )
        next_cursor = None
        if len(hits) > limit:
            hits = hits[:limit]
            next_cursor = SearchCursor(hits[-1].score, hits[-1].item_id)
        return SearchPage(hits, next_cursor)


def _search_params(filters, query, cursor, limit):
    return {
        "owner_id": filters.owner_id,
        "exclude_item_id": filters.exclude_item_id,
        "topic_id": filters.topic_id,
        "project_id": filters.project_id,
        "tag_id": filters.tag_id,
        "query": query,
        "substring": len(query) >= 3,
        # Identifiers with digits are exact keys. Trigram fuzzy matching of
        # such keys produces thousands of near-identical candidates and
        # distracts from the precise indexed FTS/substring hit.
        "typo": len(query) >= 4 and query.isalnum() and not any(ch.isdigit() for ch in query),
        "capture_limit": CAPTURE_SCAN_LIMIT,
        "cursor_id": cursor.item_id if cursor else None,
        "cursor_score": cursor.score if cursor else None,
        "page_size": limit + 1,
    }
