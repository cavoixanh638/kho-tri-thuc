import re
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from catalog.models import Item, Source
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from jobs.models import Job

from .models import CaptureEvent
from .source_identity import UnsafeCaptureURL, source_identity

MAX_TEXT_LENGTH = 65536
MAX_URL_LENGTH = 4096
CAPTURE_CHANNELS = ("web", "android", "windows", "share")
_REQUEST_KEY = re.compile(r"[\x21-\x7e]{1,128}")


class InvalidCapture(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class CaptureSubmission:
    kind: str
    url: str = ""
    text: str = ""
    source_channel: str = "web"
    client_sent_at: datetime | None = None
    idempotency_key: str | None = None
    target_item_id: UUID | None = None


def _validated_identity(submission):
    if (
        submission.target_item_id is not None
        and submission.kind != CaptureEvent.Kind.LINK
    ):
        raise InvalidCapture("source_requires_link")
    if submission.source_channel not in CAPTURE_CHANNELS:
        raise InvalidCapture("invalid_source_channel")
    if submission.client_sent_at is not None and timezone.is_naive(
        submission.client_sent_at
    ):
        raise InvalidCapture("invalid_client_sent_at")
    key = submission.idempotency_key
    if key is not None and not _REQUEST_KEY.fullmatch(key):
        raise InvalidCapture("invalid_idempotency_key")
    if len(submission.text) > MAX_TEXT_LENGTH or len(submission.url) > MAX_URL_LENGTH:
        raise InvalidCapture("capture_input_too_long")
    for raw in (submission.text, submission.url):
        if "\0" in raw:
            raise InvalidCapture("invalid_capture_input")
        try:
            raw.encode("utf-8")
        except UnicodeEncodeError:
            raise InvalidCapture("invalid_capture_input") from None

    if submission.kind == CaptureEvent.Kind.LINK:
        try:
            return source_identity(submission.url)
        except UnsafeCaptureURL:
            raise InvalidCapture("invalid_capture_url") from None

    if (
        submission.kind != CaptureEvent.Kind.TEXT
        or submission.url
        or not submission.text.strip()
    ):
        raise InvalidCapture("invalid_capture_input")
    return None


def submit_capture(owner, submission, *, on_created=None):
    identity = _validated_identity(submission)

    with transaction.atomic(durable=True):
        # Serialize this account's short write transaction. This protects both
        # first-source creation and retries without holding a lock across I/O.
        get_user_model().objects.select_for_update().only("pk").get(pk=owner.pk)

        if submission.idempotency_key is not None:
            existing = CaptureEvent.objects.filter(
                owner=owner,
                source_channel=submission.source_channel,
                idempotency_key=submission.idempotency_key,
            ).first()
            if existing is not None:
                if (
                    submission.target_item_id is not None
                    and existing.item_id != submission.target_item_id
                ):
                    raise InvalidCapture("idempotency_target_mismatch")
                return existing, False

        received_at = timezone.now()
        source = None
        if identity is not None:
            source = (
                Source.objects.filter(
                    item__owner=owner,
                    identity_hash=identity.identity_hash,
                    canonical_url=identity.canonical_url,
                )
                .order_by("captured_at", "pk")
                .first()
            )

        new_source = source is None and identity is not None
        new_item = source is None and submission.target_item_id is None
        if submission.target_item_id is not None:
            item = Item.objects.filter(
                pk=submission.target_item_id, owner=owner, deleted_at__isnull=True
            ).first()
            if item is None:
                raise InvalidCapture("unknown_target_item")
            if source is not None and source.item_id != item.pk:
                raise InvalidCapture("source_already_in_another_item")
            if source is None:
                source = Source.objects.create(
                    item=item,
                    original_url=submission.url,
                    canonical_url=identity.canonical_url,
                    identity_hash=identity.identity_hash,
                    platform=identity.platform,
                    platform_id=identity.platform_id,
                    captured_at=received_at,
                )
        if new_item:
            item = Item.objects.create(
                owner=owner,
                kind=submission.kind,
                note=submission.text if identity is None else "",
                saved_at=received_at,
            )
            if identity is not None:
                source = Source.objects.create(
                    item=item,
                    original_url=submission.url,
                    canonical_url=identity.canonical_url,
                    identity_hash=identity.identity_hash,
                    platform=identity.platform,
                    platform_id=identity.platform_id,
                    captured_at=received_at,
                )
        elif submission.target_item_id is None:
            item = source.item

        if new_source and submission.target_item_id is not None:
            item.source_fetch = "pending"
            item.content_extract = "pending"
            item.save(update_fields=["source_fetch", "content_extract", "updated_at"])

        event = CaptureEvent.objects.create(
            owner=owner,
            item=item,
            raw_kind=submission.kind,
            raw_text=submission.text,
            original_url=submission.url,
            source_channel=submission.source_channel,
            server_received_at=received_at,
            client_sent_at=submission.client_sent_at,
            idempotency_key=submission.idempotency_key,
        )
        if new_item or new_source:
            kind = "organize" if source is None else "fetch_source"
            input_ref = {"capture_id": str(event.pk)}
            if source is not None:
                input_ref["source_id"] = source.pk
            Job.objects.create(
                item=item,
                kind=kind,
                idempotency_key=str(item.pk)
                if new_item
                else f"{item.pk}:source:{source.pk}",
                input_ref=input_ref,
            )

        if on_created is not None:
            on_created(event)
        return event, True
