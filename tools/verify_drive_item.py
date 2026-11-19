"""Verify a stored original and unchanged capture history without logging user data.

Requires the application's Django environment. Record a baseline before an
operation with --record-baseline, then rerun without that flag to verify Drive.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def snapshot(item):
    from ingestion.models import CaptureEvent

    rows = list(
        CaptureEvent.objects.filter(item=item)
        .order_by("server_received_at", "id")
        .values("id", "server_received_at", "original_url", "raw_text")
    )
    payload = {
        "saved_at": item.saved_at.isoformat(),
        "events": [{key: str(value) for key, value in row.items()} for row in rows],
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return {
        "saved_at": payload["saved_at"],
        "event_count": len(rows),
        "capture_fingerprint": digest,
    }


class HashSink:
    def __init__(self, expected):
        self.expected, self.size = expected, 0
        self.digest = hashlib.sha256()

    def write(self, data):
        if self.size + len(data) > self.expected:
            raise ValueError("Unexpected Drive response size")
        self.size += len(data)
        self.digest.update(data)
        return len(data)


def verify(item, baseline):
    from googleapiclient.http import MediaIoBaseDownload
    from processing.thumbnail_integration import thumbnail_service
    from storage.service import storage_for_owner
    from storage.upload_job import staging_path

    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "source_fetch": item.source_fetch,
        "asset_storage": item.asset_storage,
        "capture_history_unchanged": snapshot(item) == baseline,
    }
    assets = list(item.assets.filter(role="original"))
    if item.asset_storage != "verified" or len(assets) != 1:
        raise ValueError("Expected one verified original")
    asset = assets[0]
    if not asset.size or not 0 < asset.size <= 128 * 1024 * 1024:
        raise ValueError("Verification is limited to 128 MiB")
    store = storage_for_owner(item.owner_id)
    remote = store.stat(asset)
    found = store.client.execute(
        store.client.api.files().list(
            q="trashed = false and appProperties has { key='kt_asset_id' and value='"
            + str(asset.pk)
            + "' }",
            spaces="drive",
            fields="nextPageToken,files(id)",
            pageSize=2,
        )
    )
    sink = HashSink(asset.size)
    download = MediaIoBaseDownload(
        sink,
        store.client.api.files().get_media(fileId=remote.file_id),
        chunksize=1024 * 1024,
    )
    done = False
    for _ in range((asset.size + 1024 * 1024 - 1) // (1024 * 1024) + 2):
        _, done = store.client.call(download.next_chunk)
        if done:
            break
    preview = thumbnail_service()
    report.update(
        event_count=baseline["event_count"],
        asset_count=1,
        bytes=asset.size,
        mime=asset.mime,
        sha256=asset.sha256,
        remote_matching_files=len(found.get("files", [])),
        remote_identity_unique=not found.get("nextPageToken")
        and [row["id"] for row in found.get("files", [])] == [remote.file_id],
        staging_removed=not staging_path(asset.pk).exists(),
        readback_matches=done
        and sink.size == asset.size
        and sink.digest.hexdigest() == asset.sha256,
        remote_sha256_matches=remote.sha256 == asset.sha256,
        thumbnail_cached=bool(preview and preview.get_cached(asset.pk, asset.sha256)),
        capture_history_unchanged=report["capture_history_unchanged"]
        and snapshot(item) == baseline,
        application_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
    )
    source = item.sources.first()
    if source:
        report["media"] = {
            key: value
            for key, value in source.metadata.get("video", {}).items()
            if key
            in {
                "duration",
                "width",
                "height",
                "audio",
                "processor",
                "processor_version",
            }
        }
    report["status"] = (
        "PASS"
        if all(
            report[key]
            for key in (
                "capture_history_unchanged",
                "remote_identity_unique",
                "readback_matches",
                "remote_sha256_matches",
                "staging_removed",
            )
        )
        else "FAIL"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--item", required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--record-baseline", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    import django

    django.setup()
    from catalog.models import Item

    item = Item.objects.get(
        pk=args.item, owner__username=args.owner, deleted_at__isnull=True
    )
    if args.record_baseline:
        args.baseline.write_text(
            json.dumps(snapshot(item), indent=2) + "\n", encoding="utf-8"
        )
        print("Capture baseline recorded without original input.")
        return 0
    if not args.output:
        parser.error("--output is required for verification")
    try:
        report = verify(item, json.loads(args.baseline.read_text(encoding="utf-8")))
    except Exception as error:  # noqa: BLE001 - redact transport exceptions that can embed credentials
        report = {"status": "FAIL", "error_type": type(error).__name__}
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Drive item verification", report["status"])
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
