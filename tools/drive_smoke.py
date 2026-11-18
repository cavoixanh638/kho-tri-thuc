"""Verify real Drive storage using temporary rows rolled back before returning.

Requires configured Django environment. Remote samples go to Drive Trash after
the check. Reports contain checksums and booleans, never account/file IDs or tokens.
"""

import argparse
import hashlib
import io
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "apps" / "backend"
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def samples():
    from PIL import Image
    from pypdf import PdfWriter

    image = io.BytesIO()
    Image.new("RGB", (16, 12), (40, 120, 180)).save(image, format="PNG")
    pdf = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(pdf)
    text = "Kho Tri Thức — kiểm tra kết nối Drive, giữ nguyên dấu tiếng Việt.\n"
    return [
        ("unicode.txt", "text/plain", text.encode()),
        ("sample.png", "image/png", image.getvalue()),
        ("sample.pdf", "application/pdf", pdf.getvalue()),
    ]


def check(owner_name):
    import django

    django.setup()
    from catalog.models import Item
    from django.contrib.auth import get_user_model
    from django.db import transaction
    from storage.drive import DriveError
    from storage.models import Asset
    from storage.service import storage_for_owner

    owner = get_user_model().objects.get(username=owner_name)
    storage = storage_for_owner(owner.pk)
    results = []
    cleanup_failed = False
    with transaction.atomic():
        try:
            for name, mime, payload in samples():
                item = Item.objects.create(owner=owner, kind=Item.Kind.FILE)
                asset = Asset.objects.create(
                    item=item,
                    mime=mime,
                    size=len(payload),
                    sha256=hashlib.sha256(payload).hexdigest(),
                    original_filename="KhoTriThuc-connection-check-" + name,
                )
                result = {"sample": name, "bytes": len(payload), "sha256": asset.sha256}
                try:
                    location = storage.save(asset, io.BytesIO(payload))
                    remote = storage.stat(asset)
                    downloaded = storage.client.execute(
                        storage.client.api.files().get_media(
                            fileId=location.provider_file_id
                        )
                    )
                    if downloaded != payload or remote.sha256 != asset.sha256:
                        raise RuntimeError("Readback did not match the original sample")
                    retried = storage.save(asset, io.BytesIO(payload))
                    if retried.provider_file_id != location.provider_file_id:
                        raise RuntimeError("Retry changed the remote file ID")
                    storage.verify(asset)
                    result.update(
                        verified=True, exact_readback=True, retry_same_file=True
                    )
                finally:
                    location = asset.locations.first()
                    result["cleanup"] = "no_remote_file"
                    if location and location.provider_file_id:
                        try:
                            # Only trash the exact file marked for this uncommitted sample.
                            storage.stat(asset)
                            storage.client.execute(
                                storage.client.api.files().update(
                                    fileId=location.provider_file_id,
                                    body={"trashed": True},
                                    fields="trashed",
                                )
                            )
                            trashed = storage.client.get_file(
                                location.provider_file_id, "trashed"
                            )
                            if not trashed.get("trashed"):
                                raise RuntimeError("Sample was not moved to Trash")
                            result["cleanup"] = "trashed"
                        except DriveError as error:
                            if error.code != "drive_not_found":
                                cleanup_failed = True
                                result["cleanup"] = "failed"
                        except RuntimeError:
                            cleanup_failed = True
                            result["cleanup"] = "failed"
                    results.append(result)
        finally:
            transaction.set_rollback(True)
    if cleanup_failed:
        raise RuntimeError("Remote sample cleanup needs attention")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", required=True, help="Local application username")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "scope": "drive.file",
    }
    try:
        report["samples"] = check(args.owner)
        report["status"] = "PASS"
        report["catalog_rows_persisted"] = False
    except Exception as error:  # noqa: BLE001 - redact exceptions that may embed credentials
        report.update(status="FAIL", error_type=type(error).__name__)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("Drive live smoke", report["status"])
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
