"""Measure private viewer reads with generated fixtures in a new disposable PostgreSQL cluster.

The optional live mode uses the existing application Drive consent in memory. It creates its
own marked QA folder and trashes only that folder at the end. The live catalogue is read-only.
"""
import argparse
import contextlib
import dataclasses
import hashlib
import io
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path
from unittest.mock import patch
from wsgiref.simple_server import WSGIRequestHandler, make_server

import psycopg


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@contextlib.contextmanager
def temporary_database(bin_dir, work):
    password = secrets.token_urlsafe(32)
    port = free_port()
    dbdir = work / "pgdata"
    pwfile = work / "initial-pg-password"
    pwfile.write_text(password, encoding="ascii")
    def pg(name, *args):
        subprocess.run([str(bin_dir / name), *map(str, args)], check=True,
                       stdout=subprocess.DEVNULL, timeout=90)
    pg("initdb", "-D", dbdir, "-U", "media_probe", "-A", "scram-sha-256",
       "--no-locale", "-E", "UTF8", "--pwfile", pwfile)
    pwfile.unlink()
    pg("pg_ctl", "-D", dbdir, "-l", work / "postgres.log", "-o",
       f"-h 127.0.0.1 -p {port}", "-w", "start")
    try:
        props = dict(host="127.0.0.1", port=port, user="media_probe", password=password)
        with psycopg.connect(dbname="postgres", **props, autocommit=True) as db:
            db.execute("CREATE DATABASE kt_media_probe")
        os.environ.update(POSTGRES_HOST="127.0.0.1", POSTGRES_PORT=str(port),
                          POSTGRES_DB="kt_media_probe", POSTGRES_USER="media_probe",
                          POSTGRES_PASSWORD=password, DJANGO_SECRET_KEY=secrets.token_urlsafe(40),
                          DJANGO_SETTINGS_MODULE="config.settings", DJANGO_ALLOWED_HOSTS="127.0.0.1,testserver")
        yield
    finally:
        pg("pg_ctl", "-D", dbdir, "-m", "fast", "-w", "stop")


def generated_sources(work, ffmpeg):
    from pypdf import PdfReader, PdfWriter
    from storage.test_pdf_page_api import pdf_fixture
    original = pdf_fixture()
    pdfs = {"pdf_small": original}
    for label, size in (("pdf_medium", 5), ("pdf_over_limit", 25)):
        writer = PdfWriter(clone_from=PdfReader(io.BytesIO(original)))
        writer.add_attachment("qa-payload.bin", b"Q" * (size * 1024 * 1024))
        stream = io.BytesIO()
        writer.write(stream)
        pdfs[label] = stream.getvalue()
    video = work / "generated.mp4"
    subprocess.run([str(ffmpeg), "-nostdin", "-loglevel", "error", "-f", "lavfi",
                    "-i", "testsrc=size=320x180:rate=15", "-t", "12", "-an", "-c:v",
                    "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", str(video)], check=True, timeout=90)
    return {**pdfs, "mp4": video.read_bytes()}


def runtime_consent(config, source_owner):
    from knowledge_pilot import source_config
    values, source = source_config(config)
    if source["host"] not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("EXPECTED_LOOPBACK_SOURCE_DB")
    if str(source["port"]) == os.environ["POSTGRES_PORT"]:
        raise ValueError("QA_MUST_USE_SEPARATE_CLUSTER")
    with psycopg.connect(**source, autocommit=True) as db:
        if db.execute("SHOW default_transaction_read_only").fetchone()[0] != "on":
            raise ValueError("SOURCE_MUST_BE_READ_ONLY")
        row = db.execute(
            "SELECT d.root_folder_id,d.refresh_token_ciphertext FROM storage_driveaccount d "
            "JOIN auth_user u ON d.owner_id=u.id WHERE u.username=%s AND d.state='connected'",
            (source_owner,),
        ).fetchone()
    if not row:
        raise ValueError("NO_CONNECTED_DRIVE_CONSENT")
    from django.test import override_settings
    from storage.drive import DriveClient, drive_credentials
    from storage.oauth import token_cipher
    approved_keys = ("GOOGLE_DRIVE_CLIENT_ID", "GOOGLE_DRIVE_CLIENT_SECRET", "GOOGLE_DRIVE_REDIRECT_URI", "GOOGLE_DRIVE_TOKEN_KEY")
    with override_settings(**{key:values[key] for key in approved_keys}):
        token = token_cipher().decrypt(row[1].encode()).decode()
        client = DriveClient(drive_credentials(token))
    return client, row[0]


@contextlib.contextmanager
def storage_probe(args, owner, report):
    from storage.drive import FOLDER_MIME
    from storage.models import DriveAccount
    from storage.service import DriveStorage
    if args.mode == "memory":
        yield None
        return
    client, app_root = runtime_consent(args.runtime_config, args.source_owner)
    root = client.get_file(app_root, "id,mimeType,trashed,appProperties")
    if root.get("trashed") or root["mimeType"] != FOLDER_MIME or root.get("appProperties", {}).get("kt_root") != "1":
        raise ValueError("APPLICATION_ROOT_MISMATCH")
    marker = uuid.uuid4().hex
    folder = client.execute(client.api.files().create(body={
        "name": f"KIEM THU MEDIA - {marker[:10]}", "parents": [app_root], "mimeType": FOLDER_MIME,
        "appProperties": {"kt_media_probe": marker}}, fields="id"))["id"]
    report["qa_folder_created"] = True
    try:
        account = DriveAccount.objects.create(owner=owner, google_user_id="qa-probe",
                                              root_folder_id=folder, state="connected")
        yield DriveStorage(client, account)
    finally:
        current = client.get_file(folder, "id,parents,appProperties")
        if current.get("parents") != [app_root] or current.get("appProperties", {}).get("kt_media_probe") != marker:
            raise ValueError("REFUSE_CLEANUP_OF_UNKNOWN_FOLDER")
        result = client.execute(client.api.files().update(fileId=folder, body={"trashed":True}, fields="trashed"))
        report["qa_folder_trashed"] = result["trashed"] is True


class QuietHandler(WSGIRequestHandler):
    def log_message(self, *args):
        pass


def measure(args, work, report):
    import django
    django.setup()
    from django.contrib.auth import get_user_model
    from django.core.management import call_command
    from django.core.wsgi import get_wsgi_application
    from django.test import Client
    from django.utils import timezone
    from PIL import Image
    from catalog.models import Item
    from storage.models import Asset, StorageLocation
    from storage.drive import DriveError

    call_command("migrate", verbosity=0, interactive=False)
    sources = generated_sources(work, args.ffmpeg)
    owner = get_user_model().objects.create_user(username="media-qa")
    foreign = get_user_model().objects.create_user(username="media-qa-foreign")
    client = Client()
    client.force_login(owner)
    other = Client()
    other.force_login(foreign)
    body_by_id = {}
    with storage_probe(args, owner, report) as drive, contextlib.ExitStack() as stack:
        reads = []
        errors = []
        requested = []
        if drive:
            observed_fields = []
            original_read = drive._read
            def inspect_remote(*args):
                remote = original_read(*args)
                observed_fields.append(remote)
                return remote
            stack.enter_context(patch.object(drive, "_read", inspect_remote))
            import requests
            original_get = requests.get
            def observed_get(*args, **kwargs):
                response = original_get(*args, **kwargs)
                report.setdefault("http_range_examples", [])
                if len(report["http_range_examples"]) < 10:
                    report["http_range_examples"].append({
                        "status":response.status_code,
                        "content_range":response.headers.get("Content-Range"),
                        "length":response.headers.get("Content-Length"),
                        "encoding":response.headers.get("Content-Encoding")})
                return response
            stack.enter_context(patch("storage.drive.requests.get", observed_get))
        class Counted:
            verifies_range_source = drive is not None and drive.verifies_range_source

            def read_range(self, asset, start, end):
                requested.append(end - start + 1)
                try:
                    result = drive.read_range(asset, start, end) if drive else body_by_id[asset.pk][start:end + 1]
                except DriveError as exc:
                    errors.append(exc.code)
                    raise
                reads.append(len(result))
                return result
        def storage_for_owner(owner_id):
            if owner_id != owner.pk:
                raise AssertionError("UNEXPECTED_OWNER_STORAGE_READ")
            return Counted()
        for module in ("pdf_page_api", "viewer_api"):
            stack.enter_context(patch("storage." + module + ".storage_for_owner", storage_for_owner))
        for name, payload in sources.items():
            if args.small_only and name != "pdf_small":
                continue
            mime = "video/mp4" if name == "mp4" else "application/pdf"
            item = Item.objects.create(owner=owner, kind="file", title=name, note="QA source note")
            asset = Asset.objects.create(item=item, mime=mime, size=len(payload),
                                        sha256=hashlib.sha256(payload).hexdigest(), content_version=1,
                                        original_filename=name + (".mp4" if name == "mp4" else ".pdf"))
            if drive:
                location = drive.save(asset, io.BytesIO(payload))
                assert location.status == "verified"
            else:
                StorageLocation.objects.create(asset=asset, provider="google_drive", provider_file_id=str(asset.pk),
                                              status="verified", verified_at=timezone.now())
                body_by_id[asset.pk] = payload
            row = {"source_bytes":len(payload), "samples":[]}
            report["sources"][name] = row
            url = f"/api/v1/assets/{asset.pk}"
            url += ("/content" if mime == "video/mp4" else "/pdf-page") + f"/1/{asset.sha256}"
            checks = (0, len(payload)//2) if mime == "video/mp4" else (1,2,3)
            for index in checks:
                reads.clear()
                requested.clear()
                errors.clear()
                if drive:
                    observed_fields.clear()
                start = time.perf_counter()
                path = url if mime == "video/mp4" else f"{url}/{index}"
                extra = {"HTTP_RANGE": f"bytes={index}-{index+511}"} if mime == "video/mp4" else {}
                response = client.get(path, **extra)
                sample = {"page_or_byte_offset":index, "http":response.status_code,
                          "elapsed_ms":round((time.perf_counter()-start)*1000,1),
                          "range_requests":len(requested), "range_reads":len(reads), "source_bytes_read":sum(reads)}
                row["samples"].append(sample)
                if errors:
                    sample["provider_error"] = errors.copy()
                    if drive:
                        sample["provider_revisions"] = [r.revision for r in observed_fields]
                        sample["comparison_differences"] = [
                            field.name for field in dataclasses.fields(observed_fields[0])
                            if any(getattr(r,field.name) != getattr(observed_fields[0],field.name)
                                   for r in observed_fields[1:])
                        ] if observed_fields else []
                    report["failed_checks"].append(name)
                    continue
                if mime == "video/mp4":
                    assert response.status_code == 206 and response.content == payload[index:index+512]
                    assert response["Content-Range"] == f"bytes {index}-{index+511}/{len(payload)}"
                elif name == "pdf_over_limit":
                    assert response.status_code == 413 and not requested
                else:
                    assert response.status_code == 200 and response["X-KT-Source-SHA256"] == asset.sha256
                    if drive is not None and index > 1:
                        assert requested == reads == [1], "Cached page must authorize one remote byte"
                    else:
                        assert sum(reads) == len(payload), "First page or unverified adapter must read the full PDF"
                    with Image.open(io.BytesIO(response.content)) as image:
                        pixel = image.convert("RGB").getpixel((image.width//2,image.height//2))
                    assert pixel == tuple(255 if channel == index-1 else 0 for channel in range(3))
                    sample["pixel_rgb"] = list(pixel)
            requested.clear()
            assert other.get(path, **extra).status_code == 404 and not requested
            assert client.get(path.replace("/1/", "/2/"), **extra).status_code == 409 and not requested
            assert Item.objects.get(pk=item.pk).note == "QA source note"
            row["foreign_owner_and_stale_denied_before_read"] = True
            if name == "mp4" and name not in report["failed_checks"]:
                with make_server("127.0.0.1", 0, get_wsgi_application(), handler_class=QuietHandler) as http:
                    thread = threading.Thread(target=http.serve_forever, daemon=True)
                    thread.start()
                    try:
                        settings = {"origin":f"http://127.0.0.1:{http.server_port}",
                                    "url":url,"cookie":client.cookies["sessionid"].value}
                        cmd = ["node", str(Path(__file__).with_name("windows_media_seek.mjs")), str(args.repo)]
                        run = subprocess.run(cmd, input=json.dumps(settings), capture_output=True, text=True,
                                             timeout=90, env={**os.environ, "KT_JOURNEY_CHROMIUM":str(args.chrome)})
                        if run.returncode:
                            raise ValueError("BROWSER_SEEK_FAILED: "+run.stderr.splitlines()[-1][:120] if run.stderr else "BROWSER_SEEK_FAILED")
                        row["browser"] = json.loads(run.stdout)
                    finally:
                        http.shutdown()
                        thread.join(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    for arg in ("pg-bin","ffmpeg","chrome","output"):
        parser.add_argument("--"+arg, type=Path, required=True)
    parser.add_argument("--mode", choices=["memory","drive"], default="memory")
    parser.add_argument("--runtime-config", type=Path)
    parser.add_argument("--source-owner")
    parser.add_argument("--small-only", action="store_true")
    args = parser.parse_args()
    if args.mode == "drive" and not (args.runtime_config and args.source_owner):
        parser.error("drive mode needs --runtime-config and the consenting --source-owner")
    args.repo = args.repo.resolve()
    sys.path[:0] = [str(args.repo/"apps/backend"),str(args.repo/"tools")]
    report = {"environment":"Windows, separate ephemeral PostgreSQL; Django test client; Chromium video element",
              "storage_mode":args.mode, "sources":{}, "status":"INCOMPLETE", "failed_checks":[]}
    modules = ["apps/backend/storage/pdf_page_api.py", "apps/backend/storage/viewer_api.py", "apps/backend/storage/drive.py", "apps/backend/storage/service.py", "apps/backend/storage/pdf_source_cache.py", "apps/backend/processing/pdfium_lock.py", "tools/smoke/windows_media_probe.py", "tools/smoke/windows_media_seek.mjs"]
    report["source_sha256"] = {path:hashlib.sha256((args.repo/path).read_bytes()).hexdigest() for path in modules}
    try:
        with tempfile.TemporaryDirectory(prefix="kt-media-qa-") as location:
            work = Path(location)
            with temporary_database(args.pg_bin, work):
                measure(args, work, report)
        report["status"] = "FAIL" if report["failed_checks"] else "PASS"
        if args.mode == "drive" and not report.get("qa_folder_trashed"):
            raise ValueError("QA_DRIVE_FOLDER_CLEANUP_NOT_CONFIRMED")
    except Exception as exc:
        report["status"] = "FAIL"
        report["failure_type"] = type(exc).__name__
        if hasattr(exc, "code"):
            report["failure_code"] = str(exc.code)
        elif isinstance(exc, ValueError) and str(exc).isupper():
            report["failure_code"] = str(exc)
        else:
            import traceback
            report["failure_site"] = [(Path(frame.filename).name,frame.lineno) for frame in traceback.extract_tb(exc.__traceback__)[-4:]]
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"status":report["status"],"mode":args.mode,"failure":report.get("failure_code", report.get("failure_site"))}))
    return int(report["status"] != "PASS")


if __name__ == "__main__":
    raise SystemExit(main())
