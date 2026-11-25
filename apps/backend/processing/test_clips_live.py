"""Opt-in public read acceptance; isolated QA DB, no private sources or writes."""

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from unittest import skipUnless

from catalog.models import Item
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TransactionTestCase

from .models import ClipAnnotation

URLS = [
    "https://docs.python.org/3/library/" + name + ".html"
    for name in ("json", "csv", "hashlib", "uuid", "datetime", "zoneinfo",
                 "pathlib", "zipfile", "tempfile", "io", "html", "html.parser",
                 "unicodedata", "dataclasses", "enum", "contextlib", "functools",
                 "collections", "textwrap", "urllib.parse")
]


@skipUnless(os.getenv("KT126_PUBLIC_READS") == "1", "Opt-in20 public source reads")
class PublicClipReads(TransactionTestCase):
    def test_twenty_public_articles_preview_and_save_without_changing_notes(self):
        self.assertEqual(str(connection.settings_dict["PORT"]), "62224")
        self.assertEqual(connection.settings_dict["NAME"], "test_kt_126_public")
        owner = get_user_model().objects.create_user(username="public-source-qa")
        self.client.force_login(owner)
        report = {"checked_at": datetime.now(UTC).isoformat(),
            "code_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "scope": "Actual20 public Python documentation read+clip; isolated QA; noDrive",
            "sources": []}
        failures = []
        for index, url in enumerate(URLS):
            item = Item.objects.create(owner=owner, kind="text", note=f"Bài biên soạn {index}\r\n")
            response = self.client.post("/api/v1/clips/preview", {
                "mode": "article", "url": url, "target_item_id": str(item.pk),
            }, content_type="application/json")
            result = response.json()
            receipt = result.get("receipt")
            actual = {"url": url, "status": response.status_code,
                "verification": result.get("verification"), "characters": len(result.get("quote", ""))}
            if result.get("verification") == "current" and receipt:
                submitted = self.client.post("/api/v1/clips", {"receipt": receipt},
                    content_type="application/json", headers={"Idempotency-Key": f"public-{index}"})
                actual["saved"] = submitted.status_code
                if submitted.status_code == 201:
                    row = ClipAnnotation.objects.get(pk=submitted.json()["annotation_id"])
                    actual["sha256"] = hashlib.sha256(row.quote.encode()).hexdigest()
                    actual["raw_note_preserved"] = Item.objects.get(pk=item.pk).note == f"Bài biên soạn {index}\r\n"
                    actual["source_excerpt_matches"] = self.client.get(f"/api/v1/clips/{row.pk}/source").json().get("quote") == row.quote
            if actual.get("saved") != 201 or not actual.get("raw_note_preserved") or not actual.get("source_excerpt_matches"):
                failures.append(url)
            report["sources"].append(actual)
        report["passed"] = len(URLS) - len(failures)
        report["executed"] = len(URLS)
        report["status"] = "PASS" if not failures else "FAIL"
        target = Path(os.environ["KT126_PUBLIC_REPORT"]).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.assertEqual(failures, [], "Only hashes/counts/publicURLs are reported; no article body inGit")
