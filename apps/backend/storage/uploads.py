import hashlib
import logging
import os
import re
from uuid import UUID, uuid4

from django.contrib.auth import get_user_model
from django.db import transaction
from ninja import File, Form, Router, Schema, Status
from ninja.files import UploadedFile
from ninja.security import django_auth

from catalog.models import Item
from jobs.models import Job
from jobs.repository import JobRepository

from .models import Asset
from .upload_job import UPLOAD_KIND, staging_path

MAX_UPLOAD_BYTES = 128 * 1024 * 1024
IDEMPOTENCY_KEY = re.compile(r"[a-zA-Z0-9_.:-]{1,128}")
CONTENT_TYPE = re.compile(r"[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+")

logger = logging.getLogger(__name__)
router = Router(auth=django_auth, tags=["Original uploads"])


class UploadReceipt(Schema):
    item_id: UUID
    asset_id: UUID
    state: str


class UploadErrorResponse(Schema):
    code: str


class UploadTooLarge(Exception):
    pass


def _remove_redundant_stage(path):
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logger.warning("Could not remove an unused upload stage %s", path.name)


def _fsync_directory(path):
    if hasattr(os, "O_DIRECTORY"):
        directory = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)


def _stage(file, asset_id):
    if file.size > MAX_UPLOAD_BYTES:
        raise UploadTooLarge

    path = staging_path(asset_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    checksum = hashlib.sha256()
    size = 0
    writer = path.open("xb")
    try:
        with writer:
            for chunk in file.chunks(chunk_size=1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise UploadTooLarge
                writer.write(chunk)
                checksum.update(chunk)
            writer.flush()
            os.fsync(writer.fileno())
        _fsync_directory(path.parent)
    except Exception:
        _remove_redundant_stage(path)
        raise
    return path, size, checksum.hexdigest()


def _job_for(owner, key):
    return Job.objects.filter(
        kind=UPLOAD_KIND, idempotency_key=key, item__owner=owner
    ).first()


def _filename(name):
    name = (name or "").replace("\\", "/").rsplit("/", 1)[-1]
    name = "".join(char for char in name if char.isprintable()).strip()
    return name[:255] if name and name not in {".", ".."} else "upload"


def _content_type(value):
    if value and len(value) <= 255 and CONTENT_TYPE.fullmatch(value):
        return value.lower()
    return "application/octet-stream"


def _record_upload(owner, file, key, asset_id, size, sha256, note=''):
    with transaction.atomic(durable=True):
        get_user_model().objects.select_for_update().only("pk").get(pk=owner.pk)
        if existing := _job_for(owner, key):
            return existing, False

        filename = _filename(file.name)
        item = Item.objects.create(owner=owner, kind=Item.Kind.FILE, title=filename, note=note)
        asset = Asset.objects.create(
            id=asset_id,
            item=item,
            mime=_content_type(file.content_type),
            size=size,
            sha256=sha256,
            original_filename=filename,
        )
        job = JobRepository.enqueue(
            kind=UPLOAD_KIND,
            idempotency_key=key,
            item=item,
            input_ref={"asset_id": str(asset.pk)},
        )
        return job, True


def accept_upload(owner, file, request_key=None, note=''):
    asset_id = uuid4()
    if request_key is None:
        key = f"asset:{asset_id}"
    else:
        digest = hashlib.sha256(f"{owner.pk}:{request_key}".encode("utf-8"))
        key = f"request:{digest.hexdigest()}"
        if existing := _job_for(owner, key):
            return existing, False

    path, size, sha256 = _stage(file, asset_id)
    # A connection failure during COMMIT can hide a successful commit.
    # Preserve the stage for the worker if the database outcome is ambiguous.
    job, created = _record_upload(owner, file, key, asset_id, size, sha256, note=note)
    if not created:
        _remove_redundant_stage(path)
    return job, created


@router.post(
    "",
    response={
        200: UploadReceipt,
        201: UploadReceipt,
        400: UploadErrorResponse,
        413: UploadErrorResponse,
        503: UploadErrorResponse,
    },
)
def upload(request, file: File[UploadedFile], note: Form[str] = ''):
    # A caption typed into the unified inbox belongs to the same file Item.
    # Reject overlong/unsafe text before creating any staging bytes or DB row.
    if len(note) > 65_536 or "\0" in note:
        return Status(400, {"code": "invalid_upload_note"})
    try:
        note.encode("utf-8")
    except UnicodeEncodeError:
        return Status(400, {"code": "invalid_upload_note"})
    request_key = request.headers.get("Idempotency-Key")
    if request_key is not None and not IDEMPOTENCY_KEY.fullmatch(request_key):
        return Status(400, {"code": "invalid_idempotency_key"})
    try:
        job, created = accept_upload(request.user, file, request_key, note=note)
    except UploadTooLarge:
        return Status(413, {"code": "upload_too_large"})
    except OSError:
        return Status(503, {"code": "upload_stage_unavailable"})
    return Status(
        201 if created else 200,
        {
            "item_id": job.item_id,
            "asset_id": job.input_ref["asset_id"],
            "state": job.state,
        },
    )
