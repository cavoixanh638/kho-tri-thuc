"""Measure real authenticated search requests against a pinned backend checkout."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from collections import Counter
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from evaluate import fingerprint, read, unique, write
from scenario_matrix import FACETS, MATRIX_FILES, in_scope, load_matrix, query_key, seed_search_cases

NEW_FILES = [HERE / name for name in ("home.json", "craft.json", "community.json")]


def fixture(suite):
    if suite == "120":
        return load_matrix(), MATRIX_FILES
    data = {"items": [], "cases": []}
    for name, path, count in zip(("home", "craft", "community"), NEW_FILES, (136, 132, 132)):
        part = read(path)
        assert len(part["cases"]) == count, path
        data["items"].extend(part["items"])
        data["cases"].extend(dict(case, suite=name) for case in part["cases"])
    items, cases = data["items"], data["cases"]
    unique([i["id"] for i in items], "item")
    unique([c["id"] for c in cases], "case")
    unique([query_key(c["query"]) for c in cases], "query")
    unique([query_key(i["note"]) for i in items], "note")
    assert all(i["note"].strip() and i["title"].strip() for i in items)
    hist = {query_key(c["query"]) for c in load_matrix()["cases"]}
    for name in ("provisional.json", "recall-check.json"):
        old = read(HERE.parent / name)
        hist.update(query_key(c["query"]) for c in old["judgments"] + old["negative_queries"])
    for path, key in ((HERE.parent / "confusable-cases/fixture.json", "cases"),
                      (HERE.parents[1] / "parallel/p16-search/corpus.json", "queries")):
        hist.update(query_key(c["query"]) for c in read(path)[key])
    assert not hist.intersection(query_key(c["query"]) for c in cases)
    blocks = Counter(c["block"] for c in cases)
    assert len(blocks) == 100 and set(blocks.values()) == {4}
    by_id = {i["id"]: i for i in items}
    for c in cases:
        expected, filters = c["accept"], c.get("filters", {})
        unique(expected, "answer")
        assert c["why"].strip() and len(c["query"]) <= 300 and c["id"].startswith(c["block"])
        assert set(filters) <= {"owner", "exclude", *FACETS}
        owner = filters.get("owner", "main")
        assert any(i.get("owner", "main") == owner for i in items)
        for key, field in FACETS.items():
            assert key not in filters or any(i.get("owner", "main") == owner and filters[key] in i.get(field, [])
                                            for i in items)
        assert "exclude" not in filters or filters["exclude"] in by_id
        assert all(i in by_id and in_scope(by_id[i], filters) for i in expected), c["id"]
        sizes = {"memory": (1,), "control": (1,), "multi": (2, 3, 4, 5), "negative": (0,)}
        assert len(expected) in sizes[c["kind"]], c["id"]
    return data, NEW_FILES


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def digest(response):
    raw = json.dumps(response, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def measure(data, backend, trial):
    if not (os.environ.get("KT_EVAL_ALLOW_DISPOSABLE") == "1"
            and os.environ.get("POSTGRES_DB") == "kt_eval_edge_pairs"
            and os.environ.get("POSTGRES_HOST") in {"127.0.0.1", "localhost", "::1"}):
        raise ValueError("Select the disposable loopback PostgreSQL QA database")
    sys.path.insert(0, str(backend / "apps/backend"))
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
    os.environ["SEARCH_MEMORY_CANDIDATES"] = "1" if trial else "0"
    import django
    django.setup()
    from catalog.models import Item
    from django.contrib.auth import get_user_model
    from django.db import connection, transaction
    from django.test import Client
    from search import reranking

    if not Path(reranking.__file__).resolve().is_relative_to(backend):
        raise RuntimeError("Not using the pinned backend checkout")
    users = get_user_model().objects
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database()")
        assert cursor.fetchone() == ("kt_eval_edge_pairs",)
    rows = []
    measured = {}
    with transaction.atomic(), ExitStack() as stack:
        if users.exists() or Item.objects.exists():
            raise RuntimeError("An empty migrated QA database is required")
        labels, filters_by_case = seed_search_cases(data)
        ids = {str(pk): label for pk, label in labels.items()}
        clients = {}
        if trial:
            original = reranking.best_addition

            def observe(query, old, extra):
                measured["candidates"] = len(extra)
                result = original(query, old, extra)
                measured["admitted"] = result is not None
                return result

            stack.enter_context(patch.object(reranking, "best_addition", side_effect=observe))
        # Start both timed runs with the same loaded local model. An unavailable
        # model would otherwise make an experiment appear equal by accident.
        if reranking.rerank_order("thử xếp hạng", ["xếp các trang bản thảo", "giàn phơi đồ"]) is None:
            raise RuntimeError("The local BGE model did not run")
        for c in data["cases"]:
            f = filters_by_case[c["id"]]
            if f.owner_id not in clients:
                client = Client(SERVER_NAME="localhost")
                client.force_login(users.get(pk=f.owner_id))
                clients[f.owner_id] = client
            client = clients[f.owner_id]
            params = {"q": c["query"], "limit": 5}
            for key in ("topic_id", "project_id", "tag_id", "exclude_item_id"):
                if (value := getattr(f, key)) is not None:
                    params[key] = str(value)
            measured.clear()
            initial = client.get("/api/v1/search", params)
            assert initial.status_code == 200, c["id"]
            default = initial.json()
            assert default["ranking"] == "lexical" and not measured
            row = {"id": c["id"], "initial": [ids[h["item_id"]] for h in default["results"]],
                   "initial_sha256": digest(default), "offered": default["can_expand"], "expanded": None}
            if row["offered"]:
                begin = time.perf_counter()
                expanded = client.get("/api/v1/search", {**params, "expand": "true"})
                elapsed = time.perf_counter() - begin
                assert expanded.status_code == 200, c["id"]
                page = expanded.json()
                row.update(expanded=[ids[h["item_id"]] for h in page["results"]], ranking=page["ranking"],
                           expanded_ms=round(elapsed * 1000, 2), **measured)
            rows.append(row)
        transaction.set_rollback(True)
    if users.exists() or Item.objects.exists():
        raise RuntimeError("Unexpected residue after rollback")
    return rows


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--suite", choices=("120", "400"), required=True)
    cli.add_argument("--backend", type=Path)
    cli.add_argument("--expected-source")
    cli.add_argument("--mode", choices=("control", "trial"))
    cli.add_argument("--output", type=Path)
    cli.add_argument("--validate", action="store_true")
    args = cli.parse_args()
    data, files = fixture(args.suite)
    if args.validate:
        print(len(data["items"]), len(data["cases"]), json.dumps(Counter(c["kind"] for c in data["cases"])))
        return
    if not all((args.backend, args.expected_source, args.mode, args.output)):
        cli.error("Provide --backend, --expected-source, --mode and a new --output")
    backend = args.backend.resolve()
    source = git(backend, "rev-parse", args.expected_source)
    if git(backend, "rev-parse", "HEAD:apps/backend") != git(backend, "rev-parse", source + ":apps/backend"):
        raise RuntimeError("Unexpected backend tree")
    if git(backend, "status", "--porcelain", "--", "apps/backend") or git(HERE, "status", "--porcelain", "--", *map(str, files)):
        raise RuntimeError("Commit the backend and fixtures before measuring")
    rows = measure(data, backend, args.mode == "trial")
    report = {"suite": args.suite, "mode": args.mode, "source": source,
              "backend_tree": git(backend, "rev-parse", source + ":apps/backend"),
              "fixtures": {f.name: fingerprint(f) for f in files}, "runner_sha256": fingerprint(Path(__file__)),
              "cases": rows}
    write(args.output, report, exclusive=True)
    print(args.suite, args.mode, "cases", len(rows), "offered", sum(r["offered"] for r in rows),
          "admitted", sum(r.get("admitted", False) for r in rows), flush=True)


if __name__ == "__main__":
    main()
