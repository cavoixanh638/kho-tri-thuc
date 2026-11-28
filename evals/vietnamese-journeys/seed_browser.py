"""Seed one new owner with the synthetic Vietnamese notes in the Windows QA database."""

import hashlib
import json
import os
from pathlib import Path


def main():
    if (os.environ.get("KT_EVAL_BROWSER_QA") != "1"
            or os.environ.get("POSTGRES_DB") != "kt_p08_journeys"
            or os.environ.get("POSTGRES_HOST") != "127.0.0.1"
            or os.environ.get("POSTGRES_PORT") != "56325"):
        raise RuntimeError("Expected the isolated Windows browser QA database")

    from django.contrib.auth import get_user_model
    from django.db import connection, transaction
    from catalog.models import Item, ItemTopic, Topic
    from catalog.organization_job import organize_item
    from jobs.models import Job

    corpus_path = Path(__file__).with_name("corpus.json")
    corpus_bytes = corpus_path.read_bytes()
    corpus = json.loads(corpus_bytes.decode("utf-8-sig"))
    username = os.environ["KT_EVAL_BROWSER_USER"]
    if not username.startswith("kt-browser-eval-"):
        raise RuntimeError("Expected a dedicated synthetic account")
    password = os.environ["KT_EVAL_BROWSER_PASSWORD"]
    seed_path = Path(os.environ["KT_EVAL_BROWSER_SEED"])
    corpus_hash = hashlib.sha256(corpus_bytes).hexdigest()
    sources = {row["id"]: row for row in corpus["items"]}
    reuse = os.environ.get("KT_EVAL_BROWSER_REUSE") == "1"
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), inet_server_port()")
            if cursor.fetchone() != ("kt_p08_journeys", 56325):
                raise RuntimeError("Unexpected PostgreSQL database or port")
        users = get_user_model().objects
        if reuse:
            seed = json.loads(seed_path.read_text(encoding="utf-8-sig"))
            owner = users.select_for_update().get(username=username)
            item_ids = seed["items"]
            inventory = {str(item.pk): item for item in Item.objects.filter(owner=owner)}
            if (not owner.check_password(password) or seed["corpus_sha256"] != corpus_hash
                    or set(item_ids) != set(sources) or set(item_ids.values()) != set(inventory)
                    or len(item_ids) != len(inventory)):
                raise RuntimeError("Credentials or inventory do not match the synthetic pilot")
            items = {key: inventory[item_id] for key, item_id in item_ids.items()}
            for key, item in items.items():
                row = sources[key]
                if (item.kind, item.title, item.note, item.deleted_at) != (
                    Item.Kind.TEXT, row["title"], row["note"], None
                ):
                    raise RuntimeError("Synthetic note changed; refusing to reorganize it")
        else:
            owner = users.create_user(username=username, password=password)
            items = {
                key: Item.objects.create(owner=owner, kind=Item.Kind.TEXT,
                                         title=row["title"], note=row["note"])
                for key, row in sources.items()
            }
            item_ids = {key: str(item.pk) for key, item in items.items()}
        for name in corpus["topics"]:
            Topic.objects.get_or_create(owner=owner, parent=None, name=name)
        for item in items.values():
            organize_item(Job(item=item, kind="organize"))
        assigned = ItemTopic.objects.filter(item__owner=owner, origin=ItemTopic.Origin.AUTO)
        print(f"Pilot: {len(items)} synthetic notes, {len(corpus['topics'])} topics, "
              f"{assigned.count()} automatic memberships on {assigned.values('item_id').distinct().count()} notes")
    if not reuse:
        seed_path.write_text(json.dumps({
            "corpus_sha256": corpus_hash,
            "items": item_ids,
        }) + "\n", encoding="utf-8")


main()
