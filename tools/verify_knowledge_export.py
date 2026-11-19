"""Verify real knowledge export without logging source text or Drive IDs.

Default is read-only. --exercise explicitly enables one existing user item,
round-trips Markdown/TXT/Markdown, withdraws only its managed derivative, and
enables it again. It never edits the Item, CaptureEvents, groups or originals.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def verify(item, record):
    from googleapiclient.http import MediaIoBaseDownload
    from processing.knowledge import snapshot
    from storage.knowledge_export import DriveKnowledge
    from storage.oauth import client_for_owner
    from verify_drive_item import HashSink

    current = snapshot(item.pk, record.format)
    if current.blocked or not current.body or record.status != "synced":
        raise ValueError("Export is not readable and synced")
    client, account = client_for_owner(item.owner_id)
    adapter = DriveKnowledge(client, account)
    remote = adapter.read(record.provider_file_id, item.pk)
    mime = "text/markdown" if record.format == "markdown" else "text/plain"
    if not adapter.matches(remote, current.body, mime, current.version):
        raise ValueError("Export metadata mismatch")
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
        raise ValueError("Export readback mismatch")
    found = client.execute(
        client.api.files().list(
            q="trashed=false and appProperties has { key='kt_knowledge' and value='1' } "
            + "and appProperties has { key='kt_item_id' and value='"
            + str(item.pk)
            + "' }",
            spaces="drive",
            pageSize=2,
            fields="nextPageToken,files(id)",
        )
    )
    if found.get("nextPageToken") or [row["id"] for row in found.get("files", [])] != [
        record.provider_file_id
    ]:
        raise ValueError("Managed export is not unique")
    return {
        "format": record.format,
        "mime": remote["mimeType"],
        "bytes": sink.size,
        "sha256": sha,
        "exact_readback": True,
        "unique_active_file": True,
        "versions_match": current.version
        == record.source_version
        == record.exported_version,
        "truncated": current.truncated,
        "video_transcript_warning": "CHƯA CÓ TRANSCRIPT VIDEO"
        in current.body.decode("utf-8"),
    }


def wait(item, desired, timeout):
    from jobs.models import Job
    from storage.models import KnowledgeExport

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        record = KnowledgeExport.objects.get(item=item)
        if record.status == desired:
            return record
        if (
            record.status == "failed"
            and not Job.objects.filter(
                item=item,
                kind="export_knowledge",
                state__in=["queued", "retry", "running"],
            ).exists()
        ):
            raise RuntimeError("Export worker failed: " + record.last_error)
        time.sleep(1)
    raise TimeoutError("Export worker did not settle")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--item", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--exercise", action="store_true")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--runtime-source", type=Path)
    parser.add_argument(
        "--preview",
        type=Path,
        help="Only write a private local preview; no Drive calls or opt-in",
    )
    args = parser.parse_args()
    if args.preview and args.exercise:
        parser.error("Preview and exercise must be separate actions")
    import django

    django.setup()
    from catalog.models import Item
    from processing.knowledge_sync import configure
    from storage.knowledge_export import DriveKnowledge
    from storage.models import KnowledgeExport
    from storage.oauth import client_for_owner
    from verify_drive_item import snapshot as capture_snapshot

    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "status": "FAIL",
        "verifier_sha": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, timeout=5
        ).strip(),
        "checks": [],
    }
    try:
        if args.runtime_source:
            report["runtime_source_sha"] = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=args.runtime_source,
                text=True,
                timeout=5,
            ).strip()
        item = Item.objects.get(
            pk=args.item, owner__username=args.owner, deleted_at__isnull=True
        )
        if args.preview:
            from processing.knowledge import snapshot as knowledge_snapshot

            preview = args.preview.resolve()
            if preview == ROOT or ROOT in preview.parents:
                raise ValueError("Private preview must remain outside Git")
            body = knowledge_snapshot(item.pk)
            preview.write_bytes(body.body)
            report.update(
                status="PREVIEW_ONLY",
                stage="local_preview",
                bytes=len(body.body),
                blocked=body.blocked,
                notes_present=bool(item.note),
                groups_count=item.itemtopic_set.count()
                + item.itemproject_set.count()
                + item.itemtag_set.count(),
                derived_count=item.derived_content.filter(status="active").count(),
                capture_events=item.captures.count(),
                assets=item.assets.count(),
                source_urls=item.sources.count(),
                drive_calls=0,
                opted_in=False,
            )
            args.output.write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8"
            )
            print("Private local preview ready; no export enabled or Drive calls made.")
            return 0
        before = capture_snapshot(item)
        originals = list(
            item.assets.order_by("id").values(
                "id", "sha256", "size", "original_filename"
            )
        )
        identity = None
        formats = (
            ["markdown", "text", "markdown"]
            if args.exercise
            else [KnowledgeExport.objects.get(item=item).format]
        )
        for format in formats:
            report["stage"] = "export_" + format
            if args.exercise:
                configure(item, enabled=True, format=format)
            record = wait(item, "synced", args.timeout)
            if identity is not None and identity != record.provider_file_id:
                raise ValueError("Format change replaced file identity")
            identity = record.provider_file_id
            report["checks"].append(verify(item, record))
            print("Verified export format", format, flush=True)
        if args.exercise:
            report["stage"] = "withdraw_and_restore"
            configure(item, enabled=False, format="markdown")
            record = wait(item, "disabled", args.timeout)
            client, account = client_for_owner(item.owner_id)
            if (
                not DriveKnowledge(client, account)
                .read(record.provider_file_id, item.pk)
                .get("trashed")
            ):
                raise ValueError("Managed derivative was not withdrawn")
            configure(item, enabled=True, format="markdown")
            record = wait(item, "synced", args.timeout)
            if identity != record.provider_file_id:
                raise ValueError("Restore replaced file identity")
            report["checks"].append(verify(item, record))
            report["withdraw_and_restore_same_id"] = True
        item.refresh_from_db()
        report["capture_history_unchanged"] = before == capture_snapshot(item)
        report["original_catalog_unchanged"] = originals == list(
            item.assets.order_by("id").values(
                "id", "sha256", "size", "original_filename"
            )
        )
        report["same_file_across_all_checks"] = True
        if (
            not report["capture_history_unchanged"]
            or not report["original_catalog_unchanged"]
            or not all(row["versions_match"] for row in report["checks"])
        ):
            raise ValueError("Source invariants or versions changed")
        report["status"], report["stage"] = "PASS", "complete"
    except Exception as error:  # noqa: BLE001 - never export private exception strings
        report["error_type"] = type(error).__name__
        code = getattr(error, "code", "")
        if isinstance(code, str) and re.fullmatch(
            r"(?:drive|knowledge)_[a-z_]{1,50}", code
        ):
            report["error_code"] = code
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Knowledge live verification", report["status"])
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
