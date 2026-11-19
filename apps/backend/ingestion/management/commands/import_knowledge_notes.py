"""Import explicitly selected Markdown articles through the normal capture service."""

import hashlib
import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from processing.knowledge_sync import PILOT_LIMIT, configure
from storage.models import KnowledgeExport

from ingestion.models import CaptureEvent
from ingestion.services import MAX_TEXT_LENGTH, CaptureSubmission, submit_capture


class Command(BaseCommand):
    help = "Preview Markdown articles; --apply imports them as text knowledge. Existing user edits are preserved."

    def add_arguments(self, parser):
        parser.add_argument("files", nargs="+", type=Path)
        parser.add_argument("--owner", required=True)
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--export", action="store_true")
        parser.add_argument("--report", type=Path)

    def handle(self, *args, **options):
        owner = get_user_model().objects.get(username=options["owner"])
        articles = []
        keys = set()
        for path in options["files"]:
            if path.suffix.casefold() not in {".md", ".markdown"}:
                raise CommandError("Expected Markdown files")
            body = path.read_bytes().decode("utf-8-sig")
            if not body.strip() or len(body) > MAX_TEXT_LENGTH or "\x00" in body:
                raise CommandError("Invalid or oversized Markdown article")
            key = "knowledge-note:" + hashlib.sha256(path.name.encode()).hexdigest()
            if key in keys:
                raise CommandError("Duplicate article filename")
            keys.add(key)
            prior = (
                CaptureEvent.objects.filter(
                    owner=owner, source_channel="windows", idempotency_key=key
                )
                .select_related("item")
                .first()
            )
            if prior and (prior.raw_text != body or prior.item.deleted_at):
                raise CommandError(
                    "Article already imported with different content or deleted; edit/restore it in the library"
                )
            articles.append((path, key, body, prior))
        if options["export"]:
            enabled = KnowledgeExport.objects.filter(
                item__owner=owner, enabled=True
            ).count()
            extra = sum(
                not prior
                or not KnowledgeExport.objects.filter(
                    item=prior.item, enabled=True
                ).exists()
                for _, _, _, prior in articles
            )
            if enabled + extra > PILOT_LIMIT:
                raise CommandError("knowledge_pilot_limit")
        report = {
            "status": "PREVIEW",
            "articles": len(articles),
            "created": 0,
            "reused": 0,
            "exports_requested": options["export"],
            "filenames": [path.name for path, _, _, _ in articles],
        }
        if options["apply"]:
            for path, key, body, _ in articles:
                event, created = submit_capture(
                    owner,
                    CaptureSubmission(
                        kind="text",
                        text=body,
                        source_channel="windows",
                        idempotency_key=key,
                    ),
                )
                if created:
                    item = event.item
                    item.title = body.strip().splitlines()[0].lstrip("# ")[:512]
                    item.save(update_fields=["title", "updated_at"])
                if options["export"]:
                    configure(event.item, enabled=True, format="markdown")
                report["created" if created else "reused"] += 1
            report["status"] = "IMPORTED"
        if options["report"]:
            options["report"].write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        self.stdout.write(json.dumps(report, ensure_ascii=False))
