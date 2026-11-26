"""Build the synthetic 10k index, or measure three warm stages with a real QA SearchService."""

import argparse
import hashlib
import os
import platform
import sys
import time
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import numpy as np
import onnxruntime

from fetch_models import MODELS
from models import Embedding, Reranker
from references import REPO, app_tree, read, write
from scale import build_corpus, build_index, measure


def database_benchmark(index, encoder, reranker, samples):
    if (os.environ.get("POSTGRES_DB") != "kt_eval_edge_pairs"
            or os.environ.get("POSTGRES_HOST") not in ("127.0.0.1", "localhost", "::1")
            or os.environ.get("KT_EVAL_ALLOW_DISPOSABLE") != "1"):
        raise RuntimeError("Use the isolated loopback kt_eval_edge_pairs QA database")
    sys.path.insert(0, str(REPO / "apps/backend"))
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
    import django
    django.setup()
    from catalog.models import Item
    from django.contrib.auth import get_user_model
    from django.db import connection, transaction
    from search.services import SearchFilters, SearchService

    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database(), current_setting('server_version')")
        database, version = cursor.fetchone()
        if database != "kt_eval_edge_pairs" or connection.vendor != "postgresql":
            raise RuntimeError("Unexpected database")
    users = get_user_model().objects
    with transaction.atomic():
        if users.exists() or Item.objects.exists():
            raise RuntimeError("Use a migrated empty QA database")
        owner = users.create_user(username="kt-semantic-10k")
        rows = []
        for n, text in enumerate(build_corpus()):
            title, note = text.split("\n", 1)
            rows.append(Item(
                id=uuid5(NAMESPACE_URL, f"urn:kt-semantic-scale:{n}"), kind=Item.Kind.TEXT,
                owner=owner, title=title, note=note,
            ))
        Item.objects.bulk_create(rows, batch_size=250)
        positions = {row.pk: i for i, row in enumerate(rows)}
        if Item.objects.filter(owner=owner).count() != 10000:
            raise RuntimeError("Incomplete test corpus")
        # The transaction's 10k uncommitted notes are not visible to autovacuum.
        with connection.cursor() as cursor:
            cursor.execute("ANALYZE catalog_item")
        service = SearchService()
        filters = SearchFilters(owner.pk)

        def lexical(query):
            page = service.search(filters, query, limit=5)
            if page.can_expand:
                page = service.search(filters, query, expand=True, limit=5)
            return [positions[hit.item_id] for hit in page.hits]

        result = measure(index, encoder.encode, reranker.score, samples, lexical=lexical)
        transaction.set_rollback(True)
    if users.exists() or Item.objects.exists():
        raise RuntimeError("QA fixture rollback failed")
    return {**result, "postgresql_version": version, "rolled_back": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("build", "measure"))
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()
    model_hash = hashlib.sha256((Path(__file__).parent / "models.py").read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    model_id = MODELS["embedding"][1] + ":" + model_hash
    report = {"model_id": model_id, "reranker_revision": MODELS["reranker"][1], "threads": args.threads,
              "backend_tree": app_tree(), "onnxruntime": onnxruntime.__version__, "python": platform.python_version()}
    encoder = Embedding(args.models, args.threads)
    if args.phase == "build":
        checkpoint = args.index.with_suffix(".json")
        previous = read(checkpoint)["next_row"] if checkpoint.exists() else 0
        start = time.perf_counter()
        index = build_index(encoder.encode, args.index, args.batch_size, model_id=model_id)
        report.update(index_build_seconds=time.perf_counter() - start, previous_rows=previous,
                      batch_size=args.batch_size, rows=int(index.shape[0]), dimension=int(index.shape[1]))
    else:
        state = read(args.index.with_suffix(".json"))
        corpus_sha = hashlib.sha256("\0".join(build_corpus()).encode("utf-8")).hexdigest()
        if state["model_id"] != model_id or state["next_row"] != 10000 or state["corpus_sha256"] != corpus_sha:
            raise ValueError("Use the matching completed 10k index")
        index = np.load(args.index, mmap_mode="r", allow_pickle=False)
        reranker = Reranker(args.models, args.threads)
        report.update(database_benchmark(index, encoder, reranker, args.samples))
        report["corpus_sha256"] = corpus_sha
    write(args.output, report, exclusive=True)
    print("10k", args.phase, report.get("index_build_seconds"), report.get("latency", {}), flush=True)


if __name__ == "__main__":
    main()
