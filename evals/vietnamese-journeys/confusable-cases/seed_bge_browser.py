"""Seed a disposable browser QA database with the frozen Vietnamese search matrix."""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from evaluate import fingerprint, write
from scenario_matrix import MATRIX_FILES, load_matrix, seed_search_cases


def main():
    if (
        os.environ.get("KT_EVAL_BROWSER_QA") != "1"
        or os.environ.get("POSTGRES_DB") != "kt_eval_bge_browser"
        or os.environ.get("POSTGRES_HOST") != "127.0.0.1"
        or os.environ.get("POSTGRES_PORT") != "56325"
    ):
        raise RuntimeError("Use the dedicated loopback kt_eval_bge_browser database on port 56325")

    from catalog.models import Item, ItemTopic, Topic
    from django.contrib.auth import get_user_model
    from django.db import connection, transaction

    fixture = load_matrix()
    case_id = os.environ.get("KT_EVAL_BROWSER_CASE", "L16")
    case = next(case for case in fixture["cases"] if case["id"] == case_id)
    users = get_user_model().objects
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            if cursor.fetchone() != ("kt_eval_bge_browser",):
                raise RuntimeError("Unexpected database")
        if users.exists() or Item.objects.exists():
            raise RuntimeError("Expected an empty migrated browser database")
        labels, filters = seed_search_cases(fixture)
        owner = users.get(pk=filters[case_id].owner_id)
        owner.set_password(os.environ["KT_EVAL_BROWSER_PASSWORD"])
        owner.save(update_fields=["password"])
        topic = Topic.objects.create(owner=owner, name="QA BGE")
        # Apply one real filter without changing the fixture's searchable scope.
        ItemTopic.objects.bulk_create([
            ItemTopic(item_id=item_id, topic=topic, origin="user")
            for item_id in Item.objects.filter(owner=owner).values_list("id", flat=True)
        ])
        write(Path(os.environ["KT_EVAL_BROWSER_SEED"]), {
            "fixture_sha256": {path.name: fingerprint(path) for path in MATRIX_FILES},
            "username": owner.username,
            "case": case_id,
            "query": case["query"],
            "topic_id": str(topic.pk),
            "target": case["accept"][0],
            "items": {str(pk): label for pk, label in labels.items()},
        }, exclusive=True)


main()
