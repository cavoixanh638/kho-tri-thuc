import json
from pathlib import Path
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import transaction

from catalog.models import Item, ItemProject, ItemTopic, Project, RelatedItem, Topic
from catalog.organization_job import organize_item, search_candidates
from jobs.models import Job

EVAL_ROOT = Path(__file__).resolve().parent
corpus = json.loads((EVAL_ROOT / "corpus.json").read_text(encoding="utf-8"))


def run():
    with transaction.atomic():
        owner = get_user_model().objects.create(username="eval-" + uuid4().hex[:12])
        topics = [
            "Chuyển đổi số",
            "Quy hoạch đô thị",
            "Bảo vệ môi trường",
            "Năng lượng tái tạo",
            "An toàn lao động",
            "Giáo dục",
        ]
        projects = [
            "Thư viện cộng đồng",
            "Đường xanh",
            "Sông sạch",
            "Mái nhà xanh",
            "Nhà máy an toàn",
        ]
        for name in topics:
            Topic.objects.create(owner=owner, name=name)
        for name in projects:
            Project.objects.create(owner=owner, name=name)
        items = {
            entry["id"]: Item.objects.create(
                owner=owner,
                kind=Item.Kind.TEXT,
                title=entry["label"],
                note=entry["text"],
            )
            for entry in corpus["items"]
        }
        expected = {
            key: set(entry["expected"])
            for key, entry in zip(items, corpus["items"], strict=True)
        }
        truth = {
            frozenset((items[entry["id"]].pk, items[entry["related_peer"]].pk))
            for entry in corpus["items"]
            if entry["related_peer"]
        }
        found = {}
        retrieved = set()
        for key, item in items.items():
            retrieved.update(
                frozenset((item.pk, peer))
                for peer in search_candidates(item, (item.title, item.note))
            )
            job = Job.objects.create(
                kind="organize", item=item, idempotency_key="eval:" + str(item.pk)
            )
            organize_item(job)
            found[key] = set(
                ItemTopic.objects.filter(item=item).values_list(
                    "topic__name", flat=True
                )
            ) | {
                "project:" + name
                for name in ItemProject.objects.filter(item=item).values_list(
                    "project__name", flat=True
                )
            }
        predicted = {
            frozenset((a, b))
            for a, b in RelatedItem.objects.filter(
                item_a__owner=owner, status=RelatedItem.Status.ACTIVE
            ).values_list("item_a_id", "item_b_id")
        }
        total_assigned = sum(map(len, found.values()))
        assignment_correct = sum(len(found[key] & expected[key]) for key in found)
        total_expected = sum(map(len, expected.values()))
        report = {
            "status": "PROVISIONAL_MODEL_AUTHORED_FIXTURES",
            "unexpected_assignments": {
                key: sorted(found[key] - expected[key])
                for key in found
                if found[key] - expected[key]
            },
            "items": len(items),
            "assignment_precision": assignment_correct / total_assigned
            if total_assigned
            else None,
            "assignment_expected_coverage": assignment_correct / total_expected
            if total_expected
            else None,
            "false_project_assignments": sum(
                len(
                    {
                        group
                        for group in found[key] - expected[key]
                        if group.startswith("project:")
                    }
                )
                for key in found
            ),
            "unclassified_items": sum(not groups for groups in found.values()),
            "candidate_recall_for_declared_pairs": len(retrieved & truth) / len(truth),
            "related_precision": len(predicted & truth) / len(predicted)
            if predicted
            else None,
            "related_expected_coverage": len(predicted & truth) / len(truth),
            "expected_related_pairs": len(truth),
            "predicted_related_pairs": len(predicted),
            "thresholds": {"min_shared_tokens": 6, "min_similarity": 1.0},
            "human_signoff": "NOT_RUN",
            "real_corpus_eval": "NOT_RUN",
        }
        transaction.set_rollback(True)
        return report


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
