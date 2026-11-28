"""Organize the four public articles and existing Golf source without copying Items."""

import hashlib
import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from ingestion.models import CaptureEvent
from processing.source_cleaning import source_metadata, source_text
from storage.models import Asset

from catalog.knowledge_tree import save_node, tree
from catalog.models import Item, ItemTopic, ItemTopicExclusion, Source

ARTICLES = {
    "giao-dich-va-tac-vu-nen.md": [
        ("Công nghệ và vận hành", "library"),
        ("Lập trình", "field"),
        ("Phát triển ứng dụng", "series"),
        ("Django", "book"),
        ("Giao dịch và tác vụ nền", "chapter"),
    ],
    "sao-luu-va-khoi-phuc.md": [
        ("Công nghệ và vận hành", "library"),
        ("Cơ sở dữ liệu", "field"),
        ("PostgreSQL", "series"),
        ("Vận hành PostgreSQL", "book"),
        ("Sao lưu và khôi phục", "chapter"),
    ],
    "quyen-google-drive.md": [
        ("Công nghệ và vận hành", "library"),
        ("Tích hợp dữ liệu", "field"),
        ("Google Drive", "series"),
        ("Kết nối và quyền truy cập", "book"),
    ],
    "van-ban-tieng-viet-va-unicode.md": [
        ("Công nghệ và vận hành", "library"),
        ("Xử lý văn bản", "field"),
        ("Unicode", "series"),
        ("Văn bản tiếng Việt", "book"),
    ],
}
GOLF = [
    ("Thể thao", "library"),
    ("Golf", "field"),
    ("Kỹ thuật short game", "series"),
    ("Cú đánh lob", "book"),
]


class Command(BaseCommand):
    help = "Preview the starter hierarchy and source metadata cleanup; --apply writes without copying content or changing capture history."

    def add_arguments(self, parser):
        parser.add_argument("--owner", required=True)
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        owner = get_user_model().objects.get(username=options["owner"])
        selected = []
        for filename, path in ARTICLES.items():
            key = "knowledge-note:" + hashlib.sha256(filename.encode()).hexdigest()
            event = (
                CaptureEvent.objects.filter(
                    owner=owner,
                    source_channel="windows",
                    idempotency_key=key,
                    item__deleted_at__isnull=True,
                )
                .select_related("item")
                .first()
            )
            if event:
                selected.append((event.item, path))
        for item in Item.objects.filter(
            owner=owner,
            deleted_at__isnull=True,
            sources__original_url="https://www.facebook.com/share/r/1A9TXTDqw5/",
        ).distinct():
            selected.append((item, GOLF))
        report = {
            "status": "PREVIEW",
            "selected_items": len(selected),
            "assigned_items": 0,
            "cleaned_source_records": 0,
            "cleaned_items": 0,
        }
        if options["apply"]:
            with transaction.atomic():
                get_user_model().objects.select_for_update().get(pk=owner.pk)
                for item, path in selected:
                    parent = None
                    for name, kind in path:
                        node, _ = save_node(
                            owner.pk, name=name, node_kind=kind, parent_id=parent
                        )
                        parent = node.pk
                    if ItemTopicExclusion.objects.filter(item=item, topic_id=parent).exists():
                        continue
                    ItemTopic.objects.update_or_create(
                        item=item,
                        topic_id=parent,
                        defaults={
                            "origin": "user",
                            "user_pinned": True,
                            "confidence": None,
                            "method_version": "",
                            "source_version": "",
                        },
                    )
                    report["assigned_items"] += 1
                for source in Source.objects.filter(item__owner=owner):
                    cleaned = source_metadata(source.metadata)
                    if cleaned != source.metadata:
                        source.metadata = cleaned
                        source.save(update_fields=["metadata"])
                        report["cleaned_source_records"] += 1
                for item in Item.objects.filter(
                    owner=owner, sources__isnull=False
                ).distinct():
                    changed = []
                    for field in ("title", "description"):
                        value = source_text(getattr(item, field))
                        if value != getattr(item, field):
                            setattr(item, field, value)
                            changed.append(field)
                    if changed:
                        item.save(update_fields=[*changed, "updated_at"])
                        report["cleaned_items"] += 1
                # No original bytes, notes, source URLs, capture times or user edits are deleted.
                report.update(
                    status="ORGANIZED",
                    tree_nodes=len(tree(owner.pk)),
                    original_assets=Asset.objects.filter(
                        item__owner=owner, role="original"
                    ).count(),
                )
        self.stdout.write(json.dumps(report, ensure_ascii=False))
