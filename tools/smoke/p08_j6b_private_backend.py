"""Isolated J6B QA-only Django WSGI sidecar with version-pinned synthetic bytes.

Starts a SECOND WSGI process inside disposable kt-p08-ci API container on port
8001. Production Django application code and existing port 8000 are unchanged.
No Drive credentials, uploader or Internet egress are used for byte reads.
"""
import hashlib
import json
import os
from pathlib import Path
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

assert os.environ.get("P08_J6B_ISOLATED") == "YES"
assert os.environ.get("POSTGRES_DB") == "kt_p08_journeys"
assert os.environ.get("PDF_NATIVE_PAGE_NAVIGATION_VERIFIED") == "1"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from django.contrib.auth import get_user_model
from django.core.wsgi import get_wsgi_application
from django.utils import timezone
from catalog.models import Item
from processing.models import DerivedContent
from storage.models import Asset, StorageLocation
from storage import viewer_api

owner = get_user_model().objects.get(username="p08-fixture")
fixture_dir = Path("/tmp")
files = {
    "pdf": (fixture_dir / "kt-j6b-generated.pdf", "application/pdf",
            {"page": 2}, "pdf_text", "Trang 2 của PDF thử"),
    "mp4": (fixture_dir / "kt-j6b-generated.mp4", "video/mp4",
            {"start_seconds": 2.5}, "video_transcript", "Video tại 2,5 giây"),
}
assert all(row[0].is_file() for row in files.values()), "J6B_BINARY_MISSING"
body_by_id = {}
items = {}
for kind, (filepath, mime, locator, part_kind, sample_text) in files.items():
    raw = filepath.read_bytes()
    assert 500 < len(raw) < 2_000_000, "J6B_INVALID_FIXTURE_SIZE"
    digest = hashlib.sha256(raw).hexdigest()
    item = Item.objects.create(owner=owner, kind="file",
                               title="P08 J6B " + kind.upper(),
                               note="# Nội dung biên soạn gốc P08 J6B " + kind)
    asset = Asset.objects.create(
        item=item, role="original", mime=mime, original_filename="p08-fixture." + kind,
        size=len(raw), sha256=digest, content_version=1)
    StorageLocation.objects.create(
        asset=asset, provider="google_drive", provider_file_id="P08-QA-ONLY-" + str(asset.pk),
        status=StorageLocation.Status.VERIFIED, verified_at=timezone.now(),
        provider_revision="synthetic-sha256-verified")
    DerivedContent.objects.create(
        item=item, asset=asset, kind=part_kind, text=sample_text,
        source_locator=locator, processor="p08-synthetic-source",
        processor_version="sha256-test-v1", input_hash=digest, status="active")
    body_by_id[str(asset.pk)] = raw
    items[kind] = {"item_id": str(item.pk), "asset_id": str(asset.pk),
                   "sha256": digest, "length": len(raw), "locator": locator}
manifest = {"task": "P08/J6B", "synthetic_only": True, "owner": owner.username,
            "pdf_page_navigation_feature_flag": True, "items": items}
Path("/tmp/p08-j6b-private-manifest.json").write_text(
    json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


class ByteStore:
    def __init__(self, owner_pk):
        if owner_pk != owner.pk:
            raise AssertionError("J6B_CROSS_OWNER_STORAGE_READ")
    def read_range(self, asset, start, end):
        payload = body_by_id.get(str(asset.pk))
        if payload is None or asset.item.owner_id != owner.pk:
            raise AssertionError("J6B_ASSET_NOT_IN_FIXTURE")
        assert 0 <= start <= end < len(payload)
        return payload[start:end + 1]


# Patch only this QA-only WSGI process. Original app stays on port 8000.
viewer_api.storage_for_owner = ByteStore
application = get_wsgi_application()


class QuietHandler(WSGIRequestHandler):
    def log_message(self, fmt, *args):
        # Never print cookies, URLs carrying query tokens or private media content.
        pass


print(json.dumps({"task": "P08/J6B", "ready": True, "port": 8001,
                  "assets": [row["asset_id"] for row in items.values()]}), flush=True)
with make_server("0.0.0.0", 8001, application, server_class=WSGIServer,
                 handler_class=QuietHandler) as server:
    server.serve_forever()
