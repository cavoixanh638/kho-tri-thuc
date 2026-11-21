"""Operator-run catalog refresh; schedule using the deployed worker's scheduler."""
import json
import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from processing.gemini_model_catalog import update_catalog


class Command(BaseCommand):
    help = "Refresh Gemini model metadata (does not check live quota or switch OCR models)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output", default="/var/lib/kho-tri-thuc/gemini-model-catalog.json",
            help="Private snapshot path outside source control",
        )

    def handle(self, *args, **options):
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise CommandError("GEMINI_API_KEY not configured; model catalog not refreshed")
        try:
            result = update_catalog(Path(options["output"]), api_key)
        except (OSError, RuntimeError, ValueError) as exc:
            # Never print sensitive server responses, request/headers or credentials.
            raise CommandError("Gemini catalog refresh unavailable; retained last snapshot") from exc
        self.stdout.write(json.dumps(result, ensure_ascii=False))
