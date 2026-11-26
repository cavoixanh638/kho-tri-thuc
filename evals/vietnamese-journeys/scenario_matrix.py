"""Fixtures, search scopes and per-case judgments for the Vietnamese search matrix."""

import re
import unicodedata
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from evaluate import read, unique


HERE = Path(__file__).resolve().parent
FACETS = {"topic": "topics", "project": "projects", "tag": "tags"}
MATRIX_FILES = [HERE / "scenario-matrix" / f"{name}.json" for name in ("language", "values", "scope")]


def query_key(text):
    folded = unicodedata.normalize("NFKD", text.casefold().replace("đ", "d"))
    letters = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return " ".join(re.findall(r"[^\W_]+", letters))


def in_scope(item, filters):
    return (
        item.get("owner", "main") == filters.get("owner", "main")
        and not item.get("trashed", False)
        and item["id"] != filters.get("exclude")
        and all(filters[key] in item.get(field, []) for key, field in FACETS.items() if key in filters)
    )


def load_matrix():
    items, cases = [], []
    for path in MATRIX_FILES:
        fixture = read(path)
        items.extend(fixture["items"])
        cases.extend(dict(case, suite=path.stem) for case in fixture["cases"])
    if len(cases) < 100:
        raise ValueError("The matrix must contain at least 100 distinct scenarios")
    unique([item["id"] for item in items], "matrix item ID")
    unique([case["id"] for case in cases], "matrix case ID")
    unique([query_key(case["query"]) for case in cases], "normalized matrix query")
    for item in items:
        fields = {"id", "title", "description", "note", "owner", "trashed", *FACETS.values()}
        if set(item) - fields or not isinstance(item.get("trashed", False), bool):
            raise ValueError(f"Invalid item field at {item['id']}")
        for field in FACETS.values():
            if not isinstance(item.get(field, []), list):
                raise ValueError(f"Expected a list of {field} at {item['id']}")
            unique(item.get(field, []), field)

    history = read(HERE / "confusable-cases" / "fixture.json")["cases"]
    history += read(HERE.parent / "parallel" / "p16-search" / "corpus.json")["queries"]
    for path in ("provisional.json", "recall-check.json"):
        old = read(HERE / path)
        history.extend(old["judgments"] + old["negative_queries"])
    prior = {query_key(case["query"]) for case in history}
    owners = {item.get("owner", "main") for item in items}
    by_id = {item["id"]: item for item in items}
    for case in cases:
        filters = case.get("filters", {})
        owner = filters.get("owner", "main")
        if set(case) - {"id", "kind", "query", "accept", "why", "filters", "suite"}:
            raise ValueError(f"Unknown case field at {case['id']}")
        if not case["why"].strip() or not case["kind"].strip() or query_key(case["query"]) in prior:
            raise ValueError(f"Missing rationale/category or duplicate historical query at {case['id']}")
        if set(filters) - {"owner", "exclude", *FACETS} or owner not in owners:
            raise ValueError(f"Unknown filter or owner at {case['id']}")
        if "exclude" in filters and filters["exclude"] not in by_id:
            raise ValueError(f"Unknown excluded item at {case['id']}")
        for key, field in FACETS.items():
            if key in filters and not any(
                item.get("owner", "main") == owner and filters[key] in item.get(field, []) for item in items
            ):
                raise ValueError(f"Unknown {key} for this owner at {case['id']}")
        if len(case["accept"]) > 5 or any(
            item not in by_id or not in_scope(by_id[item], filters) for item in case["accept"]
        ):
            raise ValueError(f"Expected results cannot appear together in scope at {case['id']}")
    return {"items": items, "cases": cases}


def seed_search_cases(fixture):
    """Create notes and owner-local facets and resolve each case's service filters."""
    from catalog.models import Item, ItemProject, ItemTag, ItemTopic, Project, Tag, Topic
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    from search.services import SearchFilters

    owners = {
        key: get_user_model().objects.create_user(username=f"kt-eval-edge-pairs-{key}")
        for key in sorted({item.get("owner", "main") for item in fixture["items"]})
    }
    models = {"topic": (Topic, ItemTopic), "project": (Project, ItemProject), "tag": (Tag, ItemTag)}
    facet_ids = {}
    item_ids = {}
    for item in fixture["items"]:
        owner = owners[item.get("owner", "main")]
        note = Item.objects.create(
            id=uuid5(NAMESPACE_URL, "urn:kt-confusable:" + item["id"]),
            owner=owner, kind=Item.Kind.TEXT, title=item["title"], note=item["note"],
            description=item.get("description", ""), deleted_at=timezone.now() if item.get("trashed") else None,
        )
        item_ids[item["id"]] = note.pk
        for key, field in FACETS.items():
            model, assignment = models[key]
            for name in item.get(field, []):
                identity = (owner.pk, key, name)
                if identity not in facet_ids:
                    facet_ids[identity] = model.objects.create(owner=owner, name=name).pk
                assignment.objects.create(item=note, origin="user", **{f"{key}_id": facet_ids[identity]})

    filters_by_case = {}
    for case in fixture["cases"]:
        selected = case.get("filters", {})
        owner_id = owners[selected.get("owner", "main")].pk
        scoped = {f"{key}_id": facet_ids[(owner_id, key, selected[key])] for key in FACETS if key in selected}
        filters_by_case[case["id"]] = SearchFilters(
            owner_id=owner_id, exclude_item_id=item_ids.get(selected.get("exclude")), **scoped,
        )
    return {pk: key for key, pk in item_ids.items()}, filters_by_case


def assess(result_ids, case, items):
    expected = case["accept"]
    if len(expected) == 1:
        relevant = result_ids[:1] == expected
    elif expected:
        relevant = set(expected).issubset(result_ids[:5])
    else:
        relevant = not result_ids
    outside = [item_id for item_id in result_ids if not in_scope(items[item_id], case.get("filters", {}))]
    return {"pass": relevant and not outside, "out_of_scope": outside}


def judge_matrix(rows, fixture):
    by_id = {case["id"]: case for case in fixture["cases"]}
    items = {item["id"]: item for item in fixture["items"]}
    totals = {}
    for row in rows:
        case = by_id[row["id"]]
        row["suite"] = case["suite"]
        row["initial_verdict"] = assess(row["initial"], case, items)
        visible = row["expanded"] if row["offered"] else row["initial"]
        row["with_suggestions_verdict"] = assess(visible, case, items)
        for key in (case["suite"], "all"):
            counts = totals.setdefault(key, {"cases": 0, "initial_pass": 0, "with_suggestions_pass": 0})
            counts["cases"] += 1
            counts["initial_pass"] += row["initial_verdict"]["pass"]
            counts["with_suggestions_pass"] += row["with_suggestions_verdict"]["pass"]
    return totals
