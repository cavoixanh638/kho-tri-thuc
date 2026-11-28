"""Replay authenticated Vietnamese search and quote-evidence clicks on synthetic notes."""

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import secrets
import subprocess
import sys
import time
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
JOURNEYS = HERE.parent
DB = "kt_eval_edge_pairs"
SUITES = ("120", "400", "48", "36")
LOOPBACK = {"127.0.0.1", "::1"}
FILTERS = ("topic_id", "project_id", "tag_id", "exclude_item_id")
EXTRA_FIXTURES = {"48": "holdout-48.json", "36": "contrast-36.json"}


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def file_sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def load_suite(suite):
    sys.path.insert(0, str(JOURNEYS))
    from scenario_matrix import FACETS, in_scope

    if suite in EXTRA_FIXTURES:
        path = HERE / EXTRA_FIXTURES[suite]
        data, files = read(path), [path]
    else:
        spec = importlib.util.spec_from_file_location(
            "memory_400_runner", JOURNEYS / "memory-400" / "run.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        data, files = module.fixture(suite)

    items = {item["id"]: item for item in data["items"]}
    cases = data["cases"]
    if len(cases) != int(suite) or len({case["id"] for case in cases}) != len(cases):
        raise ValueError(f"Unexpected or duplicate case IDs for suite {suite}")
    if len(items) != len(data["items"]):
        raise ValueError(f"Duplicate item IDs for suite {suite}")
    audit_file = HERE / "polarity-audit.json"
    if suite == "36":
        gold = {case["id"]: case for case in cases}
    else:
        gold = read(audit_file)["suites"][suite]
        files = [*files, audit_file]
    if set(gold) - {case["id"] for case in cases}:
        raise ValueError(f"Gold case outside suite {suite}")
    for case in cases:
        scope = case.get("filters", {})
        label = gold.get(case["id"], {})
        anchors = label.get("evidence", [])
        if set(scope) - {"owner", "exclude", *FACETS} or any(
            key not in items or not in_scope(items[key], scope) for key in case["accept"]
        ):
            raise ValueError(f"Invalid gold scope for {case['id']}")
        if label and (
            label["polarity"] not in {"yes", "no", "unknown"}
            or label.get("frozen_accept", case["accept"]) != case["accept"]
            or label.get("query", case["query"]) != case["query"]
            or label.get("filters", scope) != scope
            or bool(anchors) != (label["polarity"] != "unknown")
        ):
            raise ValueError(f"Invalid answer gold for {case['id']}")
        for anchor in anchors:
            source = items[anchor["source_id"]]
            if (
                not in_scope(source, scope)
                or anchor["field"] not in {"note", "description", "title"}
                or not anchor["excerpt"]
                or anchor["excerpt"] not in source.get(anchor["field"], "")
            ):
                raise ValueError(f"Invalid gold excerpt for {case['id']}")
    return data, gold, {
        (f"quote-evidence/{path.name}" if path.parent == HERE else path.relative_to(JOURNEYS).as_posix()):
        file_sha(path) for path in files
    }


def guard_database(connection, *, lock=False):
    from django.db import transaction

    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database(), host(inet_server_addr()), current_schema()")
        db, host, schema = cursor.fetchone()
        if db != DB or host not in LOOPBACK or schema != "public":
            raise RuntimeError("Expected the migrated disposable loopback PostgreSQL database")
        if lock:
            cursor.execute("SELECT pg_try_advisory_xact_lock(661527514186)")
            if not cursor.fetchone()[0]:
                raise RuntimeError("Another quote evaluation owns this database")
        static = {"django_migrations", "django_content_type", "auth_permission"}
        tables = set(connection.introspection.table_names(cursor))
        if not {"django_migrations", "catalog_item", "django_session"} <= tables:
            raise RuntimeError("Run the app migrations against the disposable database first")
        for table in sorted(tables - static):
            quoted = connection.ops.quote_name(table)
            cursor.execute(f"SELECT 1 FROM {quoted} LIMIT 1")
            if cursor.fetchone():
                raise RuntimeError(f"A blank migrated database is required (rows in {table})")
    if lock and not transaction.get_connection().in_atomic_block:
        raise RuntimeError("The evaluator must use a rollback transaction")


def login(owner, password):
    from django.test import Client

    client = Client(SERVER_NAME="localhost", enforce_csrf_checks=True)
    path = "/api/v1/session"
    initial = client.get(path)
    if initial.status_code != 200 or initial.json()["authenticated"]:
        raise RuntimeError("Session API did not start unauthenticated")
    reply = client.post(
        path,
        {"username": owner.get_username(), "password": password},
        content_type="application/json",
        headers={"X-CSRFToken": initial.json()["csrf_token"]},
    )
    if reply.status_code != 200 or reply.json()["username"] != owner.get_username():
        raise RuntimeError("Synthetic user login failed")
    return client


def search(client, params, ids, meter=None):
    if meter is not None:
        before = meter.read()
    start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    response = client.get("/api/v1/search", params)
    elapsed_ms = (time.perf_counter_ns() - start) / 1e6
    cpu_ms = (time.process_time_ns() - cpu_start) / 1e6
    energy = None
    if meter is not None:
        after = meter.read()
        from package_energy import package_energy_delta

        energy = package_energy_delta(before, after)
    if response.status_code != 200:
        raise RuntimeError(f"Search API status {response.status_code}")
    page = response.json()
    return {
        "http_status": response.status_code,
        "elapsed_ms": round(elapsed_ms, 3),
        "process_cpu_ms": round(cpu_ms, 3),
        "page": page,
        "result_ids": [ids[hit["item_id"]] for hit in page["results"]],
        "energy": energy,
    }


def evidence_score(result, gold, items):
    page = result["page"]
    anchors = gold.get("evidence", [])
    inspected = []
    for key, hit in zip(result["result_ids"], page["results"], strict=True):
        verification = hit.get("verification")
        if verification is None:
            continue
        quotes = verification["quotes"]
        exact = bool(quotes) and all(
            quote and any(quote in items[key].get(field, "") for field in ("note", "description", "title"))
            for quote in quotes
        )
        matched = [
            anchor for anchor in anchors if anchor["source_id"] == key and any(
                quote and quote in items[key].get(anchor["field"], "")
                and (anchor["excerpt"] in quote or quote in anchor["excerpt"])
                for quote in quotes
            )
        ]
        inspected.append({"source_id": key, "answer": verification["answer"],
                          "verbatim": exact, "matched_gold_anchors": matched})
    status = page.get("quote_check", {}).get("status", "skipped")
    top = inspected[0] if inspected else None
    polarity = gold.get("polarity")
    passed = None
    if polarity == "unknown":
        passed = status == "checked" and not result["result_ids"]
    elif polarity:
        passed = bool(top and top["answer"] == polarity and top["verbatim"] and top["matched_gold_anchors"])
    return {"status": status, "verified_hits": inspected, "gold_pass": passed}


def replay(data, gold, mode, meter):
    from catalog.models import Item
    from django.contrib.auth import get_user_model
    from django.db import connection, transaction
    from django.utils import timezone as django_timezone
    from scenario_matrix import assess, seed_search_cases

    cases, items = data["cases"], {item["id"]: item for item in data["items"]}
    users = get_user_model().objects
    with transaction.atomic():
        guard_database(connection, lock=True)
        fixed = datetime(2026, 1, 1, tzinfo=timezone.utc)
        saved_at = Item._meta.get_field("saved_at")
        with patch.object(django_timezone, "now", return_value=fixed), patch.object(
            saved_at, "_get_default", return_value=fixed
        ):
            labels, scopes = seed_search_cases(data)
        ids = {str(uid): key for uid, key in labels.items()}
        sessions = {}
        for key in sorted({scope.owner_id for scope in scopes.values()}):
            user = users.get(pk=key)
            password = secrets.token_urlsafe(24)
            user.set_password(password)
            user.save(update_fields=["password"])
            sessions[key] = login(user, password)
        for case in cases:
            key = case["id"]
            scope = scopes[key]
            client = sessions[scope.owner_id]
            params = {"q": case["query"], "limit": 5}
            params.update({name: str(getattr(scope, name)) for name in FILTERS if getattr(scope, name) is not None})
            default = search(client, params, ids)
            page = default["page"]
            if page["ranking"] != "lexical" or "quote_check" in page or any(
                "verification" in hit for hit in page["results"]
            ):
                raise RuntimeError(f"Default search unexpectedly changed for {key}")
            default["search_verdict"] = assess(default["result_ids"], case, items)
            click = None
            if page["can_expand"]:
                click = search(client, {**params, "expand": "true"}, ids, meter)
                click["search_verdict"] = assess(click["result_ids"], case, items)
                click["evidence"] = evidence_score(click, gold.get(key, {}), items)
                if mode == "control" and (click["evidence"]["status"] != "skipped" or click["evidence"]["verified_hits"]):
                    raise RuntimeError(f"Quote verification ran in a control click for {key}")
            yield {
                "type": "case", "id": key, "kind": case["kind"], "query": case["query"],
                "search_gold_ids": case["accept"], "answer_gold": gold.get(key, {}).get("polarity"),
                "gold_anchors": gold.get(key, {}).get("evidence", []), "offer": page["can_expand"],
                "default": default, "click": click,
            }
        transaction.set_rollback(True)
    guard_database(connection)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=SUITES, required=True)
    parser.add_argument("--validate", action="store_true", help="Validate fixtures without PostgreSQL or models")
    parser.add_argument("--backend", type=Path, default=HERE.parents[2])
    parser.add_argument("--expected-source", default="HEAD")
    parser.add_argument("--mode", choices=("control", "feature"))
    parser.add_argument("--bge", type=Path)
    parser.add_argument("--reader-url")
    parser.add_argument("--reader-model")
    parser.add_argument("--reader-revision")
    parser.add_argument("--reader-timeout", type=int, default=45)
    parser.add_argument("--energy", action="store_true", help="Record Windows RAPL energy for each click")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    data, gold, fixture_hashes = load_suite(args.suite)
    if args.validate:
        print(f"{args.suite}: {len(data['items'])} items, {len(data['cases'])} cases, {len(gold)} answer labels")
        return
    if not (args.mode and args.bge and args.output):
        parser.error("Provide --mode, --bge and --output for a measurement")
    if args.mode == "feature":
        url = urlsplit(args.reader_url or "")
        if (url.scheme != "http" or url.hostname not in LOOPBACK or url.username is not None
                or url.path != "/v1/chat/completions" or url.query or url.fragment
                or not args.reader_model or not args.reader_revision or args.reader_timeout <= 0):
            parser.error("Feature mode needs a numerical loopback reader URL and declared model revision")
    if (os.getenv("KT_EVAL_ALLOW_DISPOSABLE") != "1" or os.getenv("POSTGRES_DB") != DB
            or os.getenv("POSTGRES_HOST") not in LOOPBACK):
        parser.error("Explicitly opt in to the migrated disposable loopback PostgreSQL database")
    backend = args.backend.resolve()
    commit = git(backend, "rev-parse", args.expected_source)
    tree = git(backend, "rev-parse", f"{commit}:apps/backend")
    if git(backend, "rev-parse", "HEAD:apps/backend") != tree or git(
        backend, "status", "--porcelain", "--", "apps/backend"
    ):
        raise RuntimeError("Check out the pinned and clean backend before measuring")

    root = backend / "apps/backend"
    sys.path.insert(0, str(root))
    os.environ.update(
        DJANGO_SETTINGS_MODULE="config.settings", DJANGO_SECRET_KEY=secrets.token_urlsafe(32),
        DJANGO_ALLOWED_HOSTS="localhost", DJANGO_DEBUG="0", TOKENIZERS_PARALLELISM="false",
        SEARCH_BGE_MODEL_DIR=str(args.bge.resolve()), SEARCH_MEMORY_CANDIDATES="0",
        SEARCH_QUOTE_EVIDENCE_ENABLED="1" if args.mode == "feature" else "0",
        SEARCH_QUOTE_READER_URL=args.reader_url or "", SEARCH_QUOTE_READER_MODEL=args.reader_model or "",
        SEARCH_QUOTE_TIMEOUT_SECONDS=str(args.reader_timeout),
    )
    import django
    from django.conf import settings
    from django.db import connection, connections
    from search import reranking
    from search.prepare_bge import MODEL_FILES, MODEL_REVISION, matches_pin

    if not Path(reranking.__file__).resolve().is_relative_to(root):
        raise RuntimeError("Wrong backend import")
    for filename, (size, sha) in MODEL_FILES.items():
        if not matches_pin(args.bge / filename, size, sha):
            raise ValueError(f"Unverified BGE file: {filename}")
    django.setup()
    try:
        if args.mode == "feature" and not getattr(settings, "SEARCH_QUOTE_EVIDENCE_ENABLED", False):
            raise RuntimeError("Selected backend does not support quote checking")
        guard_database(connection)
        if reranking.rerank_order("thử xếp hạng", ["xếp các trang bản thảo", "giàn phơi đồ"]) is None:
            raise RuntimeError("Pinned BGE inference did not run")
        meter_context = nullcontext()
        if args.energy:
            from package_energy import PackageEnergyMeter

            meter_context = PackageEnergyMeter()
        with meter_context as meter, args.output.open("x", encoding="utf-8", newline="\n") as report:
            def emit(row):
                print(json.dumps(row, ensure_ascii=False, separators=(",", ":")), file=report, flush=True)

            if meter is not None:
                meter.read()
            emit({
                "type": "metadata", "suite": args.suite, "mode": args.mode, "backend_source": commit,
                "backend_tree": tree, "fixtures": fixture_hashes, "runner_sha256": file_sha(Path(__file__)),
                "cases": len(data["cases"]), "python": platform.python_version(), "platform": platform.platform(),
                "postgres": connection.pg_version, "bge_revision": MODEL_REVISION,
                "bge_files": {name: sha for name, (_, sha) in MODEL_FILES.items()},
                "reader_model": args.reader_model, "reader_revision": args.reader_revision,
                "reader_timeout_s": args.reader_timeout if args.mode == "feature" else None,
                "external_api_fees_usd": 0, "energy_scope": "gross Intel RAPL package" if meter else None,
                "energy_helper_sha256": file_sha(HERE / "package_energy.py") if meter else None,
                "energy_setup_error": meter.last_error if meter else None,
            })
            for row in replay(data, gold, args.mode, meter):
                emit(row)
            emit({"type": "complete", "cases": len(data["cases"])})
    finally:
        connections.close_all()


if __name__ == "__main__":
    main()
