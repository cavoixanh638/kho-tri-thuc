"""J6B isolated WSGI fixture server: actual Django endpoints, generated media.

Only launched in a disposable kt_p08_journeys Compose database through the CI
step. StoragePort is injected in this ephemeral server process; application
runtime and Google Drive adapters remain unmodified.
"""
import hashlib
import json
import os
import sys
sys.path.insert(0, '/app')  # isolated QA script copied to /tmp; Django modules live under /app
import subprocess
import threading
from pathlib import Path
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server

assert os.getenv("KT_J6B_ISOLATED") == "YES"
assert os.getenv("POSTGRES_DB") == "kt_p08_journeys"
assert os.getenv("POSTGRES_HOST") == "db"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()
from django.contrib.auth import get_user_model
from django.core.wsgi import get_wsgi_application
from django.db import connection
from django.utils import timezone

from catalog.models import Item
from processing.models import DerivedContent
from storage.models import Asset, StorageLocation
from storage import viewer_api, pdf_page_api

assert connection.vendor == "postgresql"
assert connection.settings_dict["NAME"] == "kt_p08_journeys"
ROOT = Path("/tmp/p08-j6b-private-ci")
ROOT.mkdir(mode=0o700, exist_ok=True)
PASS = "j6b-only-fixture-password"
PORT = 8152


def make_pdf():
    objects = ["<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>", None]
    page_ids = []
    for number, color in enumerate(("1 0 0", "0 1 0", "0 0 1"), 1):
        text = color + " rg 0 0 612 792 re f\n1 1 1 rg BT /F1 30 Tf 50 600 Td (PAGE " + str(number) + ") Tj ET"
        objects.append("<< /Length " + str(len(text.encode("ascii"))) + " >>\nstream\n" + text + "\nendstream")
        stream = len(objects)
        objects.append("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 1 0 R >> >> /Contents " + str(stream) + " 0 R >>")
        page_ids.append(len(objects))
    objects[1] = "<< /Type /Pages /Kids [" + " ".join(str(i) + " 0 R" for i in page_ids) + "] /Count 3 >>"
    objects.append("<< /Type /Catalog /Pages 2 0 R >>")
    data = b"%PDF-1.4\n"
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data += (str(number) + " 0 obj\n" + obj + "\nendobj\n").encode("ascii")
    startxref = len(data)
    data += ("xref\n0 " + str(len(objects)+1) + "\n0000000000 65535 f \n").encode("ascii")
    for offset in offsets[1:]:
        data += (str(offset).zfill(10) + " 00000 n \n").encode("ascii")
    data += ("trailer\n<< /Size " + str(len(objects)+1) + " /Root " + str(len(objects)) + " 0 R >>\nstartxref\n" + str(startxref) + "\n%%EOF\n").encode("ascii")
    return data


pdf = make_pdf()
video = ROOT / "source.mp4"
subprocess.run([
    "ffmpeg", "-nostdin", "-loglevel", "error", "-f", "lavfi",
    "-i", "testsrc=size=320x180:rate=15", "-t", "12", "-an",
    "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt",
    "yuv420p", "-movflags", "+faststart", "-y", str(video),
], check=True, timeout=70)
mp4 = video.read_bytes()
assert len(pdf) > 500 and len(mp4) > 10000
user_model = get_user_model()
owner, created = user_model.objects.get_or_create(username="p08-j6b-owner")
owner.set_password(PASS)
owner.save(update_fields=["password"])
foreign, created = user_model.objects.get_or_create(username="p08-j6b-foreign")
foreign.set_password(PASS)
foreign.save(update_fields=["password"])

files = {}
metadata = {"status": "prepared", "scope": "isolated Django WSGI + synthetic StoragePort", "pdf_pages": 3, "mp4_duration_seconds": 12, "no_external_provider": True, "items": {}}
for kind, body, mime, locator, text in (
    ("pdf", pdf, "application/pdf", {"page": 2}, "Bằng chứng trang số 2 từ PDF thật"),
    ("mp4", mp4, "video/mp4", {"start_seconds": 2.5}, "Bằng chứng thời điểm 2,5 giây trong video"),
):
    item = Item.objects.create(owner=owner, kind="file", title="P08 J6B " + kind,
                               note="# Văn bản gốc P08 J6B " + kind)
    digest = hashlib.sha256(body).hexdigest()
    asset = Asset.objects.create(
        item=item, mime=mime, size=len(body), sha256=digest,
        original_filename="fixture-" + kind, content_version=1,
    )
    assert hashlib.sha256(body).hexdigest() == asset.sha256
    StorageLocation.objects.create(
        asset=asset, provider="google_drive",
        provider_file_id="synthetic-j6b-" + str(asset.pk),
        status="verified", verified_at=timezone.now(),
    )
    DerivedContent.objects.create(
        item=item, asset=asset, kind="pdf_page" if kind == "pdf" else "video_transcript",
        text=text, source_locator=locator, processor="synthetic-pdfium-qa",
        processor_version="p08-j6b-v1", input_hash=digest,
        status="active",
    )
    files[str(asset.pk)] = body
    metadata["items"][kind] = {
        "item_id": str(item.pk), "asset_id": str(asset.pk), "sha256": digest,
        "size": len(body), "note_sha256": hashlib.sha256(item.note.encode("utf-8")).hexdigest(),
        "page_or_seconds": locator,
    }


class SyntheticStorage:
    def read_range(self, asset, start, end):
        data = files.get(str(asset.pk))
        if data is None or end >= len(data) or start < 0 or end < start:
            raise RuntimeError("TEST_STORAGE_RANGE_INVALID")
        return data[start : end + 1]


def injected(owner_id):
    assert owner_id == owner.pk, "Unexpected storage read for different owner"
    return SyntheticStorage()


viewer_api.storage_for_owner = injected
pdf_page_api.storage_for_owner = injected
metadata_path = ROOT / "fixture.json"
metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


class ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


application = get_wsgi_application()
print("P08_J6B_PRIVATE_QA_STARTED", json.dumps({"port": PORT, "items": metadata["items"]}), flush=True)
with make_server("0.0.0.0", PORT, application, server_class=ThreadedWSGIServer,
                 handler_class=WSGIRequestHandler) as httpd:
    httpd.serve_forever()
