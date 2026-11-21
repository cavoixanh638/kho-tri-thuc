"""Versioned source quotes. Network preview never holds a database write lock."""

import hashlib
import re
from urllib.parse import parse_qsl, urlsplit
from uuid import UUID

from catalog.models import Item, Source
from django.contrib.auth import get_user_model
from django.core import signing
from django.db import transaction
from django.http import Http404
from ingestion.models import CaptureEvent
from ingestion.services import CaptureSubmission, submit_capture
from ingestion.source_identity import source_identity
from jobs.repository import JobRepository

from .models import ClipAnnotation, DerivedContent
from .source_cleaning import source_text
from .source_fetch import fetch_source

MAX_TEXT = 60_000
SALT = "knowledge-clip-preview-v1"


class ClipError(ValueError):
    pass


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def owner_item(owner, item_id):
    if item_id is None:
        return None
    try:
        return Item.objects.get(pk=item_id, owner=owner, deleted_at__isnull=True)
    except Item.DoesNotExist:
        raise Http404 from None


def safe_url(url):
    from ingestion.source_identity import UnsafeCaptureURL, source_identity

    try:
        source_identity(url)
        parsed = urlsplit(url)
        if (
            parsed.username
            or parsed.password
            or any(
                re.search(
                    r"token|secret|signature|credential|authorization|api.?key|bearer",
                    key,
                    re.IGNORECASE,
                )
                for key, _ in parse_qsl(parsed.query) + parse_qsl(parsed.fragment)
            )
        ):
            raise ValueError
    except (UnsafeCaptureURL, ValueError):
        raise ClipError("invalid_public_source_url") from None
    return url


def anchor(text, quote, start=None, end=None):
    """Offsets are Unicode code points. Ambiguous excerpts require an offset."""
    if not quote:
        return None
    if start is None:
        found = text.find(quote)
        if found < 0 or text.find(quote, found + 1) >= 0:
            return None
        start, end = found, found + len(quote)
    if type(start) is not int or type(end) is not int:
        return None
    if not 0 <= start < end <= len(text) or text[start:end] != quote:
        return None
    return {"text_start": start, "text_end": end, "offset_unit": "unicode_codepoint"}


def preview(owner, payload):
    # Reject invalid selection before any outbound fetch or expensive parsing.
    if len(payload.quote) > MAX_TEXT or "\0" in payload.quote:
        raise ClipError("invalid_quote")
    try:
        payload.quote.encode("utf-8")
    except UnicodeEncodeError:
        raise ClipError("invalid_quote") from None
    if payload.mode == "selection" and not payload.quote:
        raise ClipError("quote_required")
    target = owner_item(owner, payload.target_item_id)
    data = {
        "owner_id": owner.pk,
        "target_item_id": str(target.pk) if target else None,
        "mode": payload.mode,
        "quote": payload.quote,
        "url": "",
        "page_title": "",
        "source_version": "",
        "processor_version": "",
        "locator": {},
        "part_id": None,
        "text": "",
        "verification": "link_only",
        "truncated": False,
        "fetch_status": "not_requested",
        "http_status": None,
    }
    if payload.derived_id is not None:
        part = (
            DerivedContent.objects.select_related("item", "asset")
            .filter(
                pk=payload.derived_id,
                item__owner=owner,
                item__deleted_at__isnull=True,
                status="active",
            )
            .first()
        )
        if not part:
            raise Http404
        if target and part.item_id != target.pk:
            raise ClipError("quote_source_must_belong_to_target")
        if part.asset and part.asset.item_id != part.item_id:
            raise ClipError("quote_source_unavailable")
        if part.asset and (not part.input_hash or part.asset.sha256 != part.input_hash):
            raise ClipError("quote_source_changed")
        data["target_item_id"] = str(part.item_id)
        locator = part.source_locator if isinstance(part.source_locator, dict) else {}
        source = (
            Source.objects.filter(item=part.item, pk=locator.get("source_id")).first()
            if type(locator.get("source_id")) is int
            else None
        )
        # Files without a source URL still use an honest local evidence URL;
        # capture history stores it only as a source reference, never a public fetch.
        url = source.original_url if source else payload.url
        if not url and not part.asset_id:
            raise ClipError("quote_source_url_required")
        data.update(
            url=safe_url(url) if url else "",
            part_id=part.pk,
            source_version=part.input_hash,
            processor_version=part.processor_version,
            mode="selection",
        )
        located = anchor(part.text, payload.quote, payload.start, payload.end)
        if not located:
            raise ClipError("quote_anchor_not_unique_or_mismatched")
        for key in ("page", "start_seconds", "end_seconds"):
            if key in locator:
                located[key] = locator[key]
        data.update(locator=located, verification="current", fetch_status="local_derived")
    else:
        data["url"] = safe_url(payload.url)
        if payload.mode != "link":
            result = fetch_source(
                payload.url, timeout_seconds=8, max_body_bytes=1024 * 1024
            )
            text = source_text(result.text or "") or ""
            data["fetch_status"] = str(result.status)
            provenance = getattr(result, "provenance", None)
            data["http_status"] = getattr(provenance, "http_status", None)
            data["truncated"] = len(text) > MAX_TEXT
            if len(text) > MAX_TEXT:
                text = text[:MAX_TEXT]
            data["page_title"] = (result.metadata.title if result.metadata else "")[
                :512
            ]
            if text and result.status == "fetched":
                quote = text if payload.mode == "article" else payload.quote
                located = anchor(text, quote, payload.start, payload.end)
                data.update(
                    text=text,
                    quote=quote,
                    source_version=digest(text),
                    processor_version=result.provenance.processor_version,
                    locator=located or {},
                    verification="current" if located else "unverified",
                    processor=result.provenance.processor,
                    body_sha256=result.provenance.body_sha256,
                )
            else:
                data["verification"] = "unverified" if payload.quote else "link_only"
    if len(data["quote"]) > MAX_TEXT or "\0" in data["quote"]:
        raise ClipError("invalid_quote")
    return {
        **{
            k: data[k]
            for k in ("mode", "quote", "url", "page_title", "verification", "locator", "truncated", "fetch_status", "http_status")
        },
        "source_version": data["source_version"],
        "expires_in": 300,
        "receipt": signing.dumps(data, salt=SALT, compress=True),
    }


def submit(owner, receipt, key):
    if not key:
        raise ClipError("idempotency_key_required")
    try:
        data = signing.loads(receipt, salt=SALT, max_age=300)
    except signing.BadSignature:
        raise ClipError("clip_preview_expired_or_invalid") from None
    if data.get("owner_id") != owner.pk:
        raise Http404
    owner_item(owner, data["target_item_id"])

    def persist(event):
        part = None
        # Ingestion deduplicates by canonical identity, not the raw URL spelling.
        # Reuse that same identity when attaching evidence to an existing Source.
        identity = source_identity(data["url"]) if data["url"] else None
        source = (
            Source.objects.filter(
                item=event.item,
                canonical_url=identity.canonical_url,
                identity_hash=identity.identity_hash,
            ).order_by("pk").first()
            if identity else None
        )
        if data["part_id"] is not None:
            part = (
                DerivedContent.objects.select_for_update()
                .filter(pk=data["part_id"], item=event.item, status="active")
                .first()
            )
            if (
                not part
                or part.input_hash != data["source_version"]
                or part.processor_version != data["processor_version"]
            ):
                raise ClipError("quote_source_changed")
            if part.asset and (
                part.asset.item_id != event.item_id
                or part.asset.sha256 != data["source_version"]
            ):
                raise ClipError("quote_source_changed")
            if (
                anchor(
                    part.text,
                    data["quote"],
                    data["locator"].get("text_start"),
                    data["locator"].get("text_end"),
                )
                is None
            ):
                raise ClipError("quote_source_changed")
        elif data["text"] and source:
            part = DerivedContent.objects.filter(
                item=event.item,
                asset__isnull=True,
                kind="web_text",
                status="active",
                input_hash=data["source_version"],
                processor=data["processor"],
                processor_version=data["processor_version"],
                source_locator__source_id=source.pk,
            ).first()
            if not part:
                DerivedContent.objects.filter(
                    item=event.item,
                    asset__isnull=True,
                    kind="web_text",
                    status="active",
                    source_locator__source_id=source.pk,
                ).update(status="stale")
                part = DerivedContent.objects.create(
                    item=event.item,
                    kind="web_text",
                    text=data["text"],
                    input_hash=data["source_version"],
                    processor=data["processor"],
                    processor_version=data["processor_version"],
                    source_locator={
                        "source_id": source.pk,
                        "source_url": data["url"],
                        "body_sha256": data["body_sha256"],
                    },
                )
        ClipAnnotation.objects.create(
            item=event.item,
            capture=event,
            source=source,
            part=part,
            asset=part.asset if part else None,
            mode=data["mode"],
            quote=data["quote"],
            quote_hash=digest(data["quote"]),
            source_version=data["source_version"],
            processor_version=data["processor_version"],
            locator=data["locator"],
            source_url=data["url"],
            page_title=data["page_title"],
            verification=data["verification"],
        )

    if data["url"]:
        event, created = submit_capture(
            owner,
            CaptureSubmission(
                kind="link",
                url=data["url"],
                text=data["quote"],
                idempotency_key=key,
                target_item_id=UUID(data["target_item_id"])
                if data["target_item_id"]
                else None,
            ),
            on_created=persist,
        )
    else:
        # A quote from an already attached local file has no public URL.
        # Extend the same immutable receipt contract without inventing one.
        if not re.fullmatch(r"[\x21-\x7e]{1,128}", key):
            raise ClipError("invalid_idempotency_key")
        with transaction.atomic(durable=True):
            get_user_model().objects.select_for_update().get(pk=owner.pk)
            item = owner_item(owner, data["target_item_id"])
            if not item or not data["quote"]:
                raise ClipError("invalid_file_quote")
            event = CaptureEvent.objects.filter(
                owner=owner, source_channel="web", idempotency_key=key
            ).first()
            if event and event.item_id != item.pk:
                raise ClipError("idempotency_target_mismatch")
            created = event is None
            if created:
                event = CaptureEvent.objects.create(
                    owner=owner,
                    item=item,
                    raw_kind="text",
                    raw_text=data["quote"],
                    source_channel="web",
                    idempotency_key=key,
                )
                persist(event)
    annotation = ClipAnnotation.objects.filter(capture=event).first()
    if not annotation:
        raise ClipError("idempotency_key_used_for_another_capture")
    # A retry may only replay the *same* signed clip. Ingestion intentionally
    # deduplicates on key alone; without this comparison a different receipt
    # could silently be acknowledged as the earlier quote/source.
    if (
        annotation.item_id != event.item_id
        or annotation.mode != data["mode"]
        or annotation.quote != data["quote"]
        or annotation.source_url != data["url"]
        or annotation.source_version != data["source_version"]
        or annotation.processor_version != data["processor_version"]
        or annotation.locator != data["locator"]
        or annotation.verification != data["verification"]
        or (data["part_id"] is not None and annotation.part_id != data["part_id"])
    ):
        raise ClipError("clip_idempotency_receipt_conflict")
    return {
        "capture_id": str(event.pk),
        "item_id": str(event.item_id),
        "received_at": event.server_received_at.isoformat(),
        "state": "received",
        "annotation_id": str(annotation.pk),
        "created": created,
    }


def state(annotation):
    part = annotation.part
    if annotation.item.deleted_at or (part and part.item.deleted_at):
        return "missing"
    if annotation.verification != "current":
        return annotation.verification
    if not part:
        return "missing"
    if (
        part.item_id != annotation.item_id
        or part.status != "active"
        or part.input_hash != annotation.source_version
        or part.processor_version != annotation.processor_version
    ):
        return "stale"
    if part.asset and (
        part.asset.item_id != annotation.item_id
        or part.asset.sha256 != annotation.source_version
    ):
        return "stale"
    if (
        digest(annotation.quote) != annotation.quote_hash
        or anchor(
            part.text,
            annotation.quote,
            annotation.locator.get("text_start"),
            annotation.locator.get("text_end"),
        )
        is None
    ):
        return "stale"
    return "current"


def summary(annotation):
    return {
        "id": str(annotation.pk),
        "mode": annotation.mode,
        "quote": annotation.quote,
        "source_url": annotation.source_url,
        "page_title": annotation.page_title,
        "source_id": annotation.source_id,
        "asset_id": str(annotation.asset_id) if annotation.asset_id else None,
        "part_id": annotation.part_id,
        "source_version": annotation.source_version,
        "processor_version": annotation.processor_version,
        "quote_hash": annotation.quote_hash,
        "locator": annotation.locator,
        "state": state(annotation),
        "asset_mime": annotation.asset.mime if annotation.asset_id else None,
        "asset_version": annotation.asset.content_version
        if annotation.asset_id
        else None,
        "inserted_edit_version": annotation.inserted_edit_version,
    }


@transaction.atomic
def insert(owner, annotation_id, version):
    row = (
        ClipAnnotation.objects.select_related("part__item", "part__asset", "item")
        .filter(pk=annotation_id, item__owner=owner, item__deleted_at__isnull=True)
        .first()
    )
    if not row:
        raise Http404
    item = Item.objects.select_for_update().get(pk=row.item_id)
    if (
        item.deleted_at is not None
        or item.user_edit_version != version
        or row.inserted_edit_version is not None
        or state(row) != "current"
    ):
        raise ClipError("quote_insert_conflict")
    newline = re.search(r"\r\n|\r|\n", item.note)
    newline = newline.group() if newline else "\n"
    quoted = newline.join("> " + line for line in row.quote.splitlines())
    url = row.source_url.replace("<", "%3C").replace(">", "%3E")
    reference = (
        f"[Nguồn](<{url}>)"
        if url
        else f"Tệp nguồn: {row.asset_id}; phần trích {row.part_id}."
    )
    item.note += (newline * 2 if item.note else "") + quoted + newline + reference
    item.user_edit_version += 1
    item.save(update_fields=["note", "user_edit_version", "updated_at"])
    row.inserted_edit_version = item.user_edit_version
    row.save(update_fields=["inserted_edit_version"])
    JobRepository.enqueue(
        kind="organize",
        item=item,
        idempotency_key=f"item:{item.pk}:edit:{item.user_edit_version}:deleted:{item.deleted_at}",
        input_ref={"item_id": str(item.pk)},
    )
    return {
        "note": item.note,
        "user_edit_version": item.user_edit_version,
        "updated_at": item.updated_at.isoformat(),
    }
