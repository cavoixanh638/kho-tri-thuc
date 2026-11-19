"""Run a controlled Drive pilot in a fresh, separate PostgreSQL database.

Public-source paraphrases and authored fixtures only. The production connection
is read-only. OAuth is bound in memory to the real Drive adapter; no token is
copied to the pilot database or receipts. Run prepare, connector reads, update,
then connector reads again. Private receipts allow continuation after a session.
"""

import argparse
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "https://docs.djangoproject.com/en/5.2/topics/db/transactions/",
    "https://www.postgresql.org/docs/18/app-pgdump.html",
    "https://developers.google.com/workspace/drive/api/guides/api-specific-auth",
    "https://docs.python.org/3.13/library/unicodedata.html",
}
TABLES = (
    "catalog_item",
    "catalog_source",
    "catalog_topic",
    "catalog_project",
    "catalog_tag",
    "catalog_itemtopic",
    "catalog_itemproject",
    "catalog_itemtag",
    "ingestion_captureevent",
    "processing_derivedcontent",
    "storage_asset",
    "storage_storagelocation",
    "storage_knowledgeexport",
)


class PilotError(Exception):
    """A fixed, non-private diagnostic code."""


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def validate_target(source, target, work_dir):
    if not re.fullmatch(r"kt_pilot_[a-z0-9_]{1,40}", target["dbname"]):
        raise PilotError("invalid_pilot_database_name")
    if target["host"] not in {"127.0.0.1", "localhost", "::1"}:
        raise PilotError("pilot_database_must_be_loopback")
    loopbacks = {"127.0.0.1", "localhost", "::1"}
    same_host = (
        source["host"] == target["host"]
        or {source["host"], target["host"]} <= loopbacks
    )
    if same_host and str(source["port"]) == str(target["port"]):
        raise PilotError("pilot_requires_separate_postgres_cluster")
    resolved = work_dir.resolve()
    if resolved == ROOT or ROOT in resolved.parents:
        raise PilotError("private_receipts_must_be_outside_git")


def validate_cases(data):
    cases = data["cases"]
    if len(cases) != 8 or len({row["key"] for row in cases}) != 8:
        raise PilotError("expected_eight_distinct_cases")
    for row in cases:
        if not re.fullmatch(r"[a-z]{1,16}", row["key"]):
            raise PilotError("invalid_case_key")
        if row.get("url") and row["url"] not in SOURCES:
            raise PilotError("source_not_in_public_allowlist")
        if row["format"] not in {"text", "markdown"}:
            raise PilotError("invalid_case_format")
        if not row.get("url") and "DỮ LIỆU THỬ TỰ SOẠN" not in row["note"]:
            raise PilotError("unlabelled_fixture")
    return cases


def production_fingerprint(connection):
    """Keep source rows in memory only; persist only equality, never their hash."""
    from psycopg import sql

    digest = hashlib.sha256()
    with connection.cursor() as cursor:
        for table in TABLES:
            cursor.execute(
                sql.SQL("SELECT to_jsonb(t) FROM {} t ORDER BY id LIMIT 5001").format(
                    sql.Identifier(table)
                )
            )
            rows = cursor.fetchall()
            if len(rows) > 5000:
                raise PilotError("source_snapshot_limit_exceeded")
            digest.update(table.encode())
            for (row,) in rows:
                digest.update(json.dumps(row, sort_keys=True, default=str).encode())
    return digest.hexdigest()


def source_config(path):
    values = json.loads(path.read_text(encoding="utf-8"))["environment"]
    source = {
        "dbname": values["POSTGRES_DB"],
        "user": values["POSTGRES_USER"],
        "password": values["POSTGRES_PASSWORD"],
        "host": values["POSTGRES_HOST"],
        "port": values["POSTGRES_PORT"],
        "connect_timeout": 5,
        "options": "-c default_transaction_read_only=on -c statement_timeout=15000",
    }
    return values, source


def verify(record, client):
    from googleapiclient.http import MediaIoBaseDownload
    from processing.knowledge import snapshot
    from storage.knowledge_export import DriveKnowledge
    from storage.models import DriveAccount
    from verify_drive_item import HashSink

    current = snapshot(record.item_id, record.format)
    adapter = DriveKnowledge(client, DriveAccount.objects.get(owner=record.item.owner))
    remote = adapter.read(record.provider_file_id, record.item_id)
    mime = "text/markdown" if record.format == "markdown" else "text/plain"
    if record.status != "synced" or not adapter.matches(
        remote, current.body, mime, current.version
    ):
        raise PilotError("export_metadata_mismatch")
    if (
        current.version != record.source_version
        or current.version != record.exported_version
    ):
        raise PilotError("export_version_mismatch")
    sink = HashSink(len(current.body))
    reader = MediaIoBaseDownload(
        sink,
        client.api.files().get_media(fileId=record.provider_file_id),
        chunksize=65536,
    )
    done = False
    for _ in range(len(current.body) // 65536 + 3):
        _, done = client.call(reader.next_chunk)
        if done:
            break
    sha = hashlib.sha256(current.body).hexdigest()
    if not done or sink.size != len(current.body) or sink.digest.hexdigest() != sha:
        raise PilotError("full_readback_mismatch")
    return {
        "format": record.format,
        "bytes": sink.size,
        "sha256": sha,
        "exact_readback": True,
        "versions_match": True,
        "truncated": current.truncated,
    }


def drain():
    from jobs.models import Job
    from jobs.worker import Worker
    from processing.knowledge_sync import export_knowledge

    worker = Worker({"export_knowledge": export_knowledge})
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        active = Job.objects.filter(
            kind="export_knowledge", state__in=["queued", "retry", "running"]
        )
        if not active.exists():
            if Job.objects.filter(kind="export_knowledge", state="failed").exists():
                raise PilotError("export_job_failed")
            return
        if not worker.run_once():
            time.sleep(0.5)
    raise PilotError("export_worker_timeout")


def seed(cases, owner):
    from catalog.models import ItemProject, ItemTag, Project, Tag
    from ingestion.services import CaptureSubmission, submit_capture
    from processing.models import DerivedContent
    from storage.models import Asset

    items = {}
    for row in cases:
        submission = CaptureSubmission(
            kind="link" if row.get("url") else "text",
            url=row.get("url", ""),
            text=row["note"],
            source_channel="windows",
            idempotency_key="pilot:" + row["key"],
        )
        event, created = submit_capture(owner, submission)
        repeated, repeated_created = submit_capture(owner, submission)
        if not created or repeated_created or event.pk != repeated.pk:
            raise PilotError("capture_retry_did_not_reuse_event")
        item = event.item
        item.title = "[KT202 TEST] " + row["title"]
        item.description = "Controlled acceptance fixture; not personal content or parser/ASR quality evidence."
        item.note = row["note"]
        item.source_fetch = "done" if row.get("url") else "not_applicable"
        item.save()
        project, _ = Project.objects.get_or_create(owner=owner, name=row["project"])
        tag, _ = Tag.objects.get_or_create(owner=owner, name=row["tag"])
        ItemProject.objects.create(item=item, project=project, user_pinned=True)
        ItemTag.objects.create(item=item, tag=tag, user_pinned=True)
        if row.get("text"):
            DerivedContent.objects.create(
                item=item,
                kind=row.get("derived_kind", "web_text"),
                text=row["text"],
                source_locator=row.get("locator", {}),
                processor="pilot-curated-paraphrase"
                if row.get("url")
                else "pilot-authored-fixture",
                processor_version="1",
                input_hash=hashlib.sha256(row["text"].encode()).hexdigest(),
            )
        if row.get("video_metadata_fixture"):
            Asset.objects.create(
                item=item,
                mime="video/mp4",
                original_filename="unuploaded-fixture-metadata.mp4",
            )
        items[row["key"]] = item
    return items


def update(items, cases):
    from catalog.models import Project
    from processing.knowledge_api import status
    from processing.knowledge_sync import configure, request_sync
    from processing.models import DerivedContent
    from storage.models import KnowledgeExport

    by_key = {row["key"]: row for row in cases}
    before = {
        key: KnowledgeExport.objects.get(item=item).exported_version
        for key, item in items.items()
    }
    item = items["note"]
    item.note = by_key["note"]["updated_note"]
    item.user_edit_version += 1
    item.save(update_fields=["note", "user_edit_version", "updated_at"])
    project = Project.objects.get(owner=item.owner, name="Vận hành tin cậy")
    project.name = "Vận hành có phục hồi"
    project.save(update_fields=["name"])
    old = DerivedContent.objects.get(item=items["subtitle"], status="active")
    old.status = "stale"
    old.save(update_fields=["status"])
    text = by_key["subtitle"]["updated_text"]
    DerivedContent.objects.create(
        item=old.item,
        kind=old.kind,
        text=text,
        source_locator=old.source_locator,
        processor=old.processor,
        processor_version="2",
        input_hash=hashlib.sha256(text.encode()).hexdigest(),
    )
    stale_keys = ["note", "commit", "backup", "subtitle"]
    if not all(status(items[key])["stale"] for key in stale_keys):
        raise PilotError("changed_source_not_reported_stale")
    drain()
    for key in stale_keys:
        record = KnowledgeExport.objects.get(item=items[key])
        if record.exported_version == before[key] or status(items[key])["stale"]:
            raise PilotError("changed_source_not_synchronized")
    record = KnowledgeExport.objects.get(item=items["backup"])
    version = record.exported_version
    request_sync(record.item_id, force=True)
    drain()
    record.refresh_from_db()
    if record.exported_version != version:
        raise PilotError("retry_changed_unchanged_source_version")
    # Reversible, pilot-only format and withdrawal exercises.
    for format in ("markdown", "text"):
        configure(items["unicode"], enabled=True, format=format)
        drain()
    configure(items["page"], enabled=False, format="text")
    drain()
    yield "withdrawn"
    configure(items["page"], enabled=True, format="text")
    drain()


def audit(args, report):
    import psycopg
    import requests
    from psycopg import sql

    cases = validate_cases(json.loads(args.cases.read_text(encoding="utf-8")))
    values, source = source_config(args.runtime_config)
    target = {
        "dbname": args.target_db,
        "host": args.audit_host,
        "port": args.audit_port,
        "user": args.audit_user,
        "password": os.getenv("KT_PILOT_PASSWORD", ""),
        "connect_timeout": 5,
    }
    validate_target(source, target, args.work_dir)
    receipt_path = args.work_dir / "private-receipt.json"
    with psycopg.connect(**source, autocommit=True) as production:
        if (
            production.execute("SHOW default_transaction_read_only").fetchone()[0]
            != "on"
        ):
            raise PilotError("source_is_not_read_only")
        fingerprint = production_fingerprint(production)
        row = production.execute(
            "SELECT d.root_folder_id, d.refresh_token_ciphertext FROM storage_driveaccount d JOIN auth_user u ON d.owner_id=u.id WHERE u.username=%s AND d.state='connected'",
            (args.source_owner,),
        ).fetchone()
        if not row:
            raise PilotError("connected_source_account_missing")
        source_root, ciphertext = row
        if args.phase == "prepare":
            args.work_dir.mkdir(parents=True, exist_ok=False)
            checks = []
            for case in cases:
                if case.get("url"):
                    response = requests.get(case["url"], timeout=20)
                    response.raise_for_status()
                    if case["anchor"] not in response.text:
                        raise PilotError("public_source_anchor_missing")
                    checks.append(
                        {
                            "key": case["key"],
                            "url": case["url"],
                            "http_status": response.status_code,
                            "anchor_present": True,
                            "response_sha256": hashlib.sha256(
                                response.content
                            ).hexdigest(),
                        }
                    )
            with psycopg.connect(
                **{**target, "dbname": "postgres"}, autocommit=True
            ) as maintenance:
                maintenance.execute(
                    sql.SQL(
                        "CREATE DATABASE {} TEMPLATE template0 ENCODING 'UTF8'"
                    ).format(sql.Identifier(args.target_db))
                )
            receipt = {
                "target_db": args.target_db,
                "target_host": args.audit_host,
                "target_port": args.audit_port,
                "source_fingerprint": fingerprint,
                "cases": {},
                "report": report,
            }
            report["public_source_checks"] = checks
        else:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if (
                receipt["target_db"],
                receipt["target_host"],
                receipt["target_port"],
            ) != (args.target_db, args.audit_host, args.audit_port):
                raise PilotError("receipt_target_mismatch")
            if receipt["source_fingerprint"] != fingerprint:
                raise PilotError("source_changed_since_prepare")
            report.update(receipt["report"])
            if report.get("updates"):
                raise PilotError("updates_already_complete")
        env = {
            name: value
            for name, value in values.items()
            if name.startswith("GOOGLE_DRIVE_")
        }
        env.update(
            DJANGO_SECRET_KEY=secrets.token_urlsafe(40),
            POSTGRES_DB=target["dbname"],
            POSTGRES_HOST=target["host"],
            POSTGRES_PORT=str(target["port"]),
            POSTGRES_USER=target["user"],
            POSTGRES_PASSWORD=target["password"],
            DJANGO_SETTINGS_MODULE="config.settings",
        )
        os.environ.update(env)
        sys.path.insert(0, str(ROOT / "apps/backend"))
        import django

        django.setup()
        from catalog.models import Item
        from django.contrib.auth import get_user_model
        from django.core.management import call_command
        from ingestion.models import CaptureEvent
        from processing.knowledge_sync import configure
        from storage.drive import FOLDER_MIME, DriveClient, drive_credentials
        from storage.knowledge_export import DriveKnowledge
        from storage.models import DriveAccount, KnowledgeExport
        from storage.oauth import token_cipher

        client = DriveClient(
            drive_credentials(token_cipher().decrypt(ciphertext.encode()).decode())
        )
        if args.phase == "prepare":
            call_command("migrate", verbosity=0, interactive=False)
            owner = get_user_model().objects.create_user(
                username="kt202-controlled-pilot"
            )
            pilot_root = client.reserve_file_id()
            receipt["root_folder_id"] = pilot_root
            write_json(receipt_path, receipt)
            root = client.get_file(source_root, "id,mimeType,trashed,appProperties")
            if (
                root.get("trashed")
                or root.get("mimeType") != FOLDER_MIME
                or root.get("appProperties", {}).get("kt_root") != "1"
            ):
                raise PilotError("application_root_mismatch")
            client.execute(
                client.api.files().create(
                    body={
                        "id": pilot_root,
                        "name": "KIEM THU KT202 - " + args.target_db,
                        "mimeType": FOLDER_MIME,
                        "parents": [source_root],
                        "appProperties": {"kt_acceptance": "controlled-pilot"},
                    },
                    fields="id",
                )
            )
            DriveAccount.objects.create(
                owner=owner,
                google_user_id="controlled-pilot",
                root_folder_id=pilot_root,
                state="connected",
            )
            items = seed(cases, owner)
            receipt["cases"] = {
                key: {"item_id": str(item.pk)} for key, item in items.items()
            }
            write_json(receipt_path, receipt)
        else:
            owner = get_user_model().objects.get(username="kt202-controlled-pilot")
            items = {
                key: Item.objects.get(pk=value["item_id"], owner=owner)
                for key, value in receipt["cases"].items()
            }
        event_values = list(
            CaptureEvent.objects.order_by("id").values(
                "id", "raw_text", "original_url", "server_received_at"
            )
        )

        def bind(owner_id):
            if owner_id != owner.pk:
                raise PilotError("unexpected_pilot_owner")
            return client, DriveAccount.objects.get(owner=owner)

        with patch("processing.knowledge_sync.client_for_owner", side_effect=bind):
            if args.phase == "prepare":
                for case in cases:
                    configure(items[case["key"]], enabled=True, format=case["format"])
                drain()
            else:
                for _ in update(items, cases):
                    record = KnowledgeExport.objects.get(item=items["page"])
                    if (
                        not DriveKnowledge(*bind(owner.pk))
                        .read(record.provider_file_id, record.item_id)
                        .get("trashed")
                    ):
                        raise PilotError("pilot_withdraw_not_trashed")
                report["updates"] = {
                    "note": True,
                    "project_rename_two_items": True,
                    "subtitle_version": True,
                    "stale_visible_before_worker": True,
                    "retry_unchanged_version": True,
                    "format_roundtrip": True,
                    "withdraw_restore_same_identity": True,
                }
        results = []
        for key, item in items.items():
            record = KnowledgeExport.objects.select_related("item").get(item=item)
            previous_id = receipt["cases"][key].get("file_id")
            if previous_id and previous_id != record.provider_file_id:
                raise PilotError("export_identity_changed")
            result = {"key": key, **verify(record, client)}
            receipt["cases"][key]["file_id"] = record.provider_file_id
            results.append(result)
        account = DriveAccount.objects.get(owner=owner)
        listing = client.execute(
            client.api.files().list(
                q=f"'{account.knowledge_folder_id}' in parents and trashed=false",
                spaces="drive",
                pageSize=20,
                fields="nextPageToken,files(id)",
            )
        )
        if listing.get("nextPageToken") or {x["id"] for x in listing["files"]} != {
            x["file_id"] for x in receipt["cases"].values()
        }:
            raise PilotError("unexpected_active_export_files")
        if event_values != list(
            CaptureEvent.objects.order_by("id").values(
                "id", "raw_text", "original_url", "server_received_at"
            )
        ):
            raise PilotError("capture_history_changed")
        if production_fingerprint(production) != fingerprint:
            raise PilotError("production_catalog_changed_during_audit")
        if DriveAccount.objects.exclude(refresh_token_ciphertext="").exists():
            raise PilotError("pilot_database_contains_oauth_token")
        report.update(
            status="PASS_CONTROLLED_LIVE",
            phase=args.phase,
            checked_at=datetime.now(UTC).isoformat(),
            scope="8 controlled Items: 4 verified public-source paraphrases, 4 authored fixtures; real Drive adapter and isolated PostgreSQL",
            checks={
                "production_connection_read_only": True,
                "production_catalog_unchanged": True,
                "separate_postgres_cluster": True,
                "dedicated_marked_drive_folder": True,
                "oauth_token_not_copied_to_pilot_db": True,
                "credentials_bound_in_memory": True,
                "capture_history_unchanged": True,
                "capture_retry_reuses_event": True,
                "active_export_file_count": len(results),
                "unique_file_per_item": True,
            },
            exports=results,
            not_verified=[
                "personal corpus quality",
                "PDF parsing or video ASR",
                "native Google Docs",
                "connector retrieval: recorded separately",
            ],
        )
        receipt["report"] = report
        write_json(receipt_path, receipt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-config", type=Path, required=True)
    parser.add_argument("--source-owner", default="admin")
    parser.add_argument("--target-db", required=True)
    parser.add_argument("--audit-host", default="127.0.0.1")
    parser.add_argument("--audit-port", type=int, required=True)
    parser.add_argument("--audit-user", required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument(
        "--cases", type=Path, default=ROOT / "evals/knowledge/pilot-cases.json"
    )
    parser.add_argument("--phase", choices=["prepare", "update"], required=True)
    parser.add_argument(
        "--exercise",
        action="store_true",
        help="Explicitly authorize creation/update of pilot-only records and files",
    )
    args = parser.parse_args()
    if not args.exercise:
        parser.error("--exercise is required for the controlled live pilot")
    report = {
        "status": "FAIL",
        "phase": args.phase,
        "application_source_sha": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, timeout=5
        ).strip(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "corpus_sha256": hashlib.sha256(args.cases.read_bytes()).hexdigest(),
    }
    try:
        audit(args, report)
    except Exception as error:  # noqa: BLE001 - sanitize all external errors at the CLI boundary
        report["status"] = "FAIL"
        report["error"] = (
            str(error) if isinstance(error, PilotError) else type(error).__name__
        )
        write_json(args.report, report)
        print(json.dumps({"status": "FAIL", "error": report["error"]}))
        return 1
    write_json(args.report, report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "phase": report["phase"],
                "exports": len(report["exports"]),
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
