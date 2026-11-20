"""Provider-free review PoC: proposals are inert until explicit versioned acceptance.

Signed, expiring receipts avoid a new suggestion table for the isolated PoC.
They are POST bodies, never URLs; no provider, prompt execution or external calls.
"""

import hashlib
import json
import secrets
from dataclasses import dataclass

from catalog.models import Item
from django.core import signing
from django.db import transaction
from jobs.repository import JobRepository

MAX_NOTE = 100_000
RECEIPT_TTL = 900
SALT = "kt120-suggestion-review-v1"


class SuggestionError(ValueError):
    pass


def text_hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def source_version(item):
    evidence = {
        "sources": list(
            item.sources.order_by("pk").values("id", "original_url", "canonical_url")
        ),
        "assets": list(
            item.assets.order_by("pk").values("id", "sha256", "content_version")
        ),
        "parts": [
            [
                p.pk,
                p.status,
                p.input_hash,
                p.processor,
                p.processor_version,
                text_hash(p.text),
                p.source_locator,
            ]
            for p in item.derived_content.order_by("pk")
        ],
    }
    return text_hash(
        json.dumps(evidence, sort_keys=True, ensure_ascii=False, default=str)
    )


def validate_note(note):
    if not isinstance(note, str) or len(note) > MAX_NOTE or "\0" in note:
        raise SuggestionError("invalid_proposed_note")
    try:
        note.encode("utf-8")
    except UnicodeError:
        raise SuggestionError("invalid_proposed_note") from None


def owner_item(owner_id, item_id, *, lock=False):
    query = Item.objects.select_for_update() if lock else Item.objects.all()
    item = query.filter(pk=item_id, owner_id=owner_id, deleted_at__isnull=True).first()
    if item is None:
        raise SuggestionError("suggestion_item_unavailable")
    return item


def proposal(owner_id, item_id, after):
    validate_note(after)
    item = owner_item(owner_id, item_id)
    receipt = {
        "schema": 1,
        "action": "accept",
        "owner_id": owner_id,
        "item_id": str(item.pk),
        "source_version": source_version(item),
        "base_edit_version": item.user_edit_version,
        "before": item.note,
        "after": after,
        "nonce": secrets.token_hex(16),
        "provenance": {
            "provider": "none",
            "model": "none",
            "method": "user_supplied_poc",
            "prompt_version": "not_run",
        },
    }
    return {
        **receipt,
        "receipt": signing.dumps(receipt, salt=SALT, compress=True),
        "expires_in": RECEIPT_TTL,
    }


def read_receipt(owner_id, item_id, token, action):
    try:
        value = signing.loads(token, salt=SALT, max_age=RECEIPT_TTL)
    except signing.BadSignature:
        raise SuggestionError("suggestion_receipt_invalid_or_expired") from None
    if (
        not isinstance(value, dict)
        or value.get("schema") != 1
        or value.get("action") != action
        or value.get("owner_id") != owner_id
        or value.get("item_id") != str(item_id)
    ):
        raise SuggestionError("suggestion_receipt_scope_mismatch")
    return value


@dataclass(frozen=True)
class ReviewResult:
    note: str
    edit_version: int
    source_version: str
    undo_receipt: str = ""


def apply_note(item, note):
    item.note = note
    item.user_edit_version += 1
    item.save(update_fields=["note", "user_edit_version", "updated_at"])
    JobRepository.enqueue(
        kind="organize",
        item=item,
        idempotency_key=f"item:{item.pk}:edit:{item.user_edit_version}:deleted:{item.deleted_at}",
        input_ref={"item_id": str(item.pk)},
    )


@transaction.atomic
def accept(owner_id, item_id, token):
    value = read_receipt(owner_id, item_id, token, "accept")
    item = owner_item(owner_id, item_id, lock=True)
    current_source = source_version(item)
    if (
        item.user_edit_version != value["base_edit_version"]
        or item.note != value["before"]
        or current_source != value["source_version"]
    ):
        raise SuggestionError("suggestion_version_conflict")
    if item.note == value["after"]:
        raise SuggestionError("suggestion_has_no_change")
    apply_note(item, value["after"])
    undo = {**value, "action": "undo", "accepted_edit_version": item.user_edit_version}
    return ReviewResult(
        item.note,
        item.user_edit_version,
        current_source,
        signing.dumps(undo, salt=SALT, compress=True),
    )


def reject(owner_id, item_id, token):
    read_receipt(owner_id, item_id, token, "accept")
    owner_item(owner_id, item_id)
    # No persistence or write. This receipt is discarded by the UI.
    return {"state": "rejected", "writes": 0}


@transaction.atomic
def undo(owner_id, item_id, token):
    value = read_receipt(owner_id, item_id, token, "undo")
    item = owner_item(owner_id, item_id, lock=True)
    current_source = source_version(item)
    if (
        item.user_edit_version != value["accepted_edit_version"]
        or item.note != value["after"]
        or current_source != value["source_version"]
    ):
        raise SuggestionError("suggestion_version_conflict")
    apply_note(item, value["before"])
    return ReviewResult(item.note, item.user_edit_version, current_source)
