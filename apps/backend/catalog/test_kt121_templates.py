"""Synthetic Markdown template persistence/export tests; no external calls.

Fixtures live in this backend test so Docker API CI does not need frontend files.
Set KT121_RESTORE=1 and KT121_RESTORE_DB=test_kt121_restore on the disposable
QA cluster to additionally run a real pg_dump / fresh pg_restore proof.
"""

import hashlib
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

import psycopg
from django.contrib.auth import get_user_model
from django.core import serializers
from django.db import connection
from django.test import TransactionTestCase
from django.utils import timezone
from ingestion.models import CaptureEvent
from ingestion.services import CaptureSubmission, submit_capture
from processing.knowledge import snapshot
from processing.models import DerivedContent
from processing.read_knowledge import ReadKnowledgeService
from psycopg import sql
from storage.models import Asset, StorageLocation

from .models import Item, ItemTopic, Source, Topic

# Independent ordinary-Markdown fixtures representing the four optional patterns.
PATTERNS = {
    "lesson": "# Bài học\n\n## Ý chính\n\n\n\n## Ví dụ\n\n\n\n## Áp dụng\n\n- [ ] \n",
    "book": "# Sách / Chương\n\n## Luận điểm\n\n\n\n## Trích dẫn cần đối chiếu\n\n> \n\n## Liên hệ và ghi chú\n\n",
    "meeting": "# Cuộc họp\n\n## Nội dung trao đổi\n\n\n\n## Quyết định\n\n\n\n## Việc cần làm\n\n- [ ] \n",
    "video": "# Video nguồn\n\n## Điều quan sát được\n\n\n\n## Mốc cần đối chiếu\n\n- Thời điểm: \n\n## Ghi chú và câu hỏi\n\n",
}


class NoteTemplatePersistenceTests(TransactionTestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="kt121-synthetic")
        self.topic = Topic.objects.create(owner=self.owner, name="Bài học tổng hợp")
        self.client.force_login(self.owner)

    def exercise_matrix(self):
        expected, originals = {}, {}
        for pattern, body in PATTERNS.items():
            for index in range(10):
                with self.subTest(pattern=pattern, item=index + 1):
                    newline = ("\n", "\r\n", "\r")[index % 3]
                    raw = f"  Ghi chú {index + 1} tiếng Việt Tiếng 🧑‍🚀{newline}Dòng sau **nguyên văn**  "
                    event, created = submit_capture(
                        self.owner,
                        CaptureSubmission(kind="text", text=raw),
                    )
                    self.assertTrue(created)
                    item = event.item
                    source = Source.objects.create(
                        item=item,
                        original_url=f"https://example.org/{pattern}/{index}",
                        canonical_url=f"https://example.org/{pattern}/{index}",
                        identity_hash=hashlib.sha256(
                            f"{pattern}-{index}".encode()
                        ).hexdigest(),
                    )
                    asset = Asset.objects.create(
                        item=item,
                        mime="application/pdf",
                        original_filename=f"synthetic-{pattern}-{index}.pdf",
                        sha256="a" * 64,
                        size=100,
                    )
                    location = StorageLocation.objects.create(
                        asset=asset,
                        provider_file_id=f"synthetic-kt121-{pattern}-{index}",
                        status="verified",
                        verified_at=timezone.now(),
                    )
                    derived = DerivedContent.objects.create(
                        item=item,
                        asset=asset,
                        kind="pdf_text",
                        text="Trích nguồn riêng biệt",
                        processor="synthetic",
                        processor_version="1",
                        input_hash="b" * 64,
                        source_locator={"page": index + 1},
                    )
                    pinned = ItemTopic.objects.create(
                        item=item,
                        topic=self.topic,
                        user_pinned=True,
                        origin="user",
                    )
                    before = (
                        event.pk,
                        event.raw_text,
                        event.server_received_at,
                        item.saved_at,
                    )
                    heading, remainder = body.split("\n", 1)
                    insertion = (
                        f"{heading}\n\nTác giả: Nguyễn Thị Học {index + 1}\n"
                        f"Ngày nguồn: 2026-11-20\nLiên kết nguồn: https://example.org/nguon\n{remainder}"
                    ).replace("\n", newline)
                    note = raw + newline + newline + insertion
                    result = self.client.patch(
                        f"/api/v1/items/{item.pk}",
                        {"note": note},
                        content_type="application/json",
                    )
                    self.assertEqual(result.status_code, 200)
                    reloaded = self.client.get(f"/api/v1/items/{item.pk}").json()
                    self.assertEqual(reloaded["item_id"], str(item.pk))
                    self.assertEqual(reloaded["note"].encode(), note.encode())
                    self.assertEqual(reloaded["assets"][0]["asset_id"], str(asset.pk))
                    item.refresh_from_db()
                    self.assertEqual(item.user_edit_version, 1)
                    self.assertEqual(
                        ReadKnowledgeService().read(item)["text"].encode(),
                        note.encode(),
                    )
                    for export_format in ("markdown", "text"):
                        exported = snapshot(item.pk, export_format)
                        self.assertFalse(exported.truncated)
                        self.assertFalse(exported.blocked)
                        expected_export = (
                            re.sub(r"(?m)^#{1,6} ", "", note)
                            if export_format == "text"
                            else note
                        )
                        self.assertIn(expected_export.encode(), exported.body)
                        self.assertIn(str(item.pk).encode(), exported.body)
                        self.assertIn(location.provider_file_id.encode(), exported.body)
                    event.refresh_from_db()
                    self.assertEqual(
                        (
                            event.pk,
                            event.raw_text,
                            event.server_received_at,
                            item.saved_at,
                        ),
                        before,
                    )
                    pinned.refresh_from_db()
                    self.assertTrue(pinned.user_pinned)
                    derived.refresh_from_db()
                    self.assertEqual(derived.text, "Trích nguồn riêng biệt")
                    self.assertEqual(derived.source_locator, {"page": index + 1})
                    self.assertEqual(Source.objects.get(pk=source.pk).item_id, item.pk)
                    self.assertEqual(
                        StorageLocation.objects.get(pk=location.pk).asset_id, asset.pk
                    )
                    expected[str(item.pk)] = note
                    originals[str(event.pk)] = raw
        self.assertEqual(len(expected), 40)
        self.assertEqual(Item.objects.count(), 40)
        self.assertEqual(Asset.objects.count(), 40)
        self.assertEqual(CaptureEvent.objects.count(), 40)
        return expected, originals

    def test_forty_notes_persist_reload_export_with_stable_provenance(self):
        self.exercise_matrix()
        # Portable JSON model projection round trip; actual DB restore is a separate gate.
        encoded = serializers.serialize(
            "json", Item.objects.order_by("id"), ensure_ascii=False
        )
        restored = list(serializers.deserialize("json", encoded))
        self.assertEqual(
            [(entry.object.pk, entry.object.note.encode()) for entry in restored],
            [(item.pk, item.note.encode()) for item in Item.objects.order_by("id")],
        )

    @unittest.skipUnless(
        os.getenv("KT121_RESTORE") == "1",
        "Opt in on the disposable QA cluster for native pg_dump restore",
    )
    def test_native_dump_restore_keeps_forty_notes_and_all_mappings(self):
        expected, originals = self.exercise_matrix()
        config = connection.settings_dict
        source = config["NAME"]
        target = os.environ.get("KT121_RESTORE_DB", "test_kt121_restore")
        if source != "test_kt121" or target != "test_kt121_restore":
            self.fail(
                "Native restore proof is restricted to the two dedicated KT-121 test databases"
            )
        connect = {
            "host": config["HOST"],
            "port": config["PORT"],
            "user": config["USER"],
            "password": config["PASSWORD"],
        }
        environment = {
            **os.environ,
            "PGHOST": config["HOST"],
            "PGPORT": str(config["PORT"]),
            "PGUSER": config["USER"],
            "PGPASSWORD": config["PASSWORD"],
        }
        tables = [
            "catalog_item",
            "ingestion_captureevent",
            "catalog_source",
            "catalog_topic",
            "catalog_project",
            "catalog_tag",
            "catalog_itemtopic",
            "catalog_itemproject",
            "catalog_itemtag",
            "storage_asset",
            "storage_storagelocation",
            "processing_derivedcontent",
            "catalog_relateditem",
            "jobs_job",
            "storage_knowledgeexport",
        ]

        def rows(database):
            with psycopg.connect(dbname=database, **connect) as database_connection:
                return {
                    table: database_connection.execute(
                        sql.SQL("SELECT * FROM {} ORDER BY id").format(
                            sql.Identifier(table)
                        )
                    ).fetchall()
                    for table in tables
                }

        with psycopg.connect(
            dbname="postgres", autocommit=True, **connect
        ) as maintenance:
            if maintenance.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s", [target]
            ).fetchone():
                self.fail("Restore target already exists; refusing to overwrite it")
            maintenance.execute(
                sql.SQL("CREATE DATABASE {} TEMPLATE template0 ENCODING 'UTF8'").format(
                    sql.Identifier(target)
                )
            )
        try:
            before = rows(source)
            with tempfile.TemporaryDirectory(
                prefix="kt121-synthetic-restore-"
            ) as directory:
                archive = Path(directory) / "templates.dump"
                subprocess.run(
                    [
                        "pg_dump",
                        "--no-password",
                        "--format=custom",
                        "--no-owner",
                        "--no-privileges",
                        f"--dbname={source}",
                        f"--file={archive}",
                    ],
                    env=environment,
                    check=True,
                    capture_output=True,
                    timeout=60,
                )
                subprocess.run(
                    [
                        "pg_restore",
                        "--no-password",
                        "--single-transaction",
                        "--exit-on-error",
                        "--no-owner",
                        "--no-privileges",
                        f"--dbname={target}",
                        str(archive),
                    ],
                    env=environment,
                    check=True,
                    capture_output=True,
                    timeout=60,
                )
                self.assertEqual(rows(target), before)
                with psycopg.connect(dbname=target, **connect) as recovered:
                    notes = recovered.execute(
                        "SELECT id,note FROM catalog_item"
                    ).fetchall()
                    raw_events = recovered.execute(
                        "SELECT id,raw_text FROM ingestion_captureevent"
                    ).fetchall()
                self.assertEqual({str(pk): note for pk, note in notes}, expected)
                self.assertEqual({str(pk): text for pk, text in raw_events}, originals)
                print(
                    f"KT121 native restore: 40/40 notes, 15 collections match; dump_sha256={hashlib.sha256(archive.read_bytes()).hexdigest()}"
                )
        finally:
            with psycopg.connect(
                dbname="postgres", autocommit=True, **connect
            ) as maintenance:
                maintenance.execute(
                    sql.SQL("DROP DATABASE {} WITH (FORCE)").format(
                        sql.Identifier(target)
                    )
                )
