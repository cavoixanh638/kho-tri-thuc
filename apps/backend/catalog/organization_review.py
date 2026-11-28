"""KT129: human-reviewed deterministic organization proposals, isolated from jobs.

No AI provider, new database table, or changes to the existing OrganizationService.
Decisions use short-lived signed, owner/source-bound receipts. Accepted assignments
are user-owned so future automatic organization does not replace them. Dismissals
are session-scoped until G00 introduces a durable review ledger/migration.
"""
from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json

from django.contrib.auth import get_user_model
from django.core import signing
from django.db import transaction
from processing.models import DerivedContent

from .models import Assignment, Item, ItemProject, ItemTag, ItemTopic, ItemTopicExclusion, Project, Tag, Topic
from .organization_rules import GroupEvidence, normalize_phrase

METHOD = "kt129-catalog-rule-review-v1"
ACCEPTED_METHOD = "kt129-human-accepted-v1"
SALT = "kt129-organization-review-v1"
RECEIPT_TTL = 900
REJECT_SESSION_KEY = "kt129_review_dismissals"
MAX_SESSION_DISMISSALS = 512
GROUPS = {
    "topic": (Topic, ItemTopic),
    "project": (Project, ItemProject),
    "tag": (Tag, ItemTag),
}
LABELS = {
    "topic": ("chu de", "topic"),
    "project": ("du an", "project"),
    "tag": ("nhan", "tag"),
}
FIELDS = ("origin", "user_pinned", "confidence", "method_version", "source_version")


class ReviewError(ValueError):
    def __init__(self, code, status=409):
        super().__init__(code)
        self.code = code
        self.status = status


def _hash(value):
    return sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, default=str,
                   separators=(",", ":")).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class EvidencePart:
    field: str
    text: str
    processor: str = ""
    processor_version: str = ""
    input_hash: str = ""
    locator: object = None
    row_id: int | None = None


def _parts(item):
    parts = [
        EvidencePart("ghi chú", item.note),
        EvidencePart("mô tả", item.description),
        EvidencePart("tiêu đề", item.title),
    ]
    rows = getattr(item, "_review_derived_rows", None)
    if rows is None:
        rows = list(
            DerivedContent.objects.filter(item=item, status=DerivedContent.Status.ACTIVE)
            .exclude(text="").order_by("pk")
        )
    for row in rows:
        if row.text.strip():
            parts.append(EvidencePart(
                "nội dung trích xuất", row.text, row.processor, row.processor_version,
                row.input_hash, row.source_locator, row.pk,
            ))
    return tuple(part for part in parts if part.text and part.text.strip())


def _version(item, parts):
    return _hash({
        "kind": item.kind,
        "user_edit_version": item.user_edit_version,
        "sources": [
            [p.field, p.row_id, _hash(p.text), p.processor,
             p.processor_version, p.input_hash, p.locator]
            for p in parts
        ],
    })


def _quote(text, phrase):
    """Quote a real input line; keep its matching phrase visible when possible."""
    for line in text.splitlines():
        normalized = " " + normalize_phrase(line) + " "
        if " " + phrase + " " not in normalized:
            continue
        line = line.strip()
        if len(line) <= 220:
            return line
        # Prefer the vicinity of the first token, including accent-insensitive text.
        token = phrase.split()[0]
        words = line.split()
        start = next(
            (i for i, word in enumerate(words)
             if normalize_phrase(word) == token), 0
        )
        snippet = " ".join(words[max(0, start - 8):start + len(phrase.split()) + 13])
        return ("…" if start > 8 else "") + snippet[:220] + ("…" if len(snippet) > 220 else "")
    return ""


def _match(kind, phrase, note, parts, rules):
    if not rules.supports(kind, phrase):
        return None
    for line in note.splitlines():
        left, sep, right = line.partition(":")
        if sep and normalize_phrase(left) in LABELS[kind] and normalize_phrase(right) == phrase:
            return {
                "field": "ghi chú", "excerpt": line.strip()[:220],
                "processor": "user", "processor_version": "",
                "confidence": 1.0, "evidence_type": "explicit_declaration",
            }
    if kind == "project" or " " not in phrase:
        return None
    for part in parts:
        # Metadata alone cannot certify the contents of a captured link/media.
        if part.field not in ("ghi chú", "nội dung trích xuất"):
            continue
        if " " + phrase + " " not in " " + normalize_phrase(part.text) + " ":
            continue
        excerpt = _quote(part.text, phrase)
        if not excerpt:
            continue
        score = {
            "ghi chú": 0.8, "nội dung trích xuất": 0.65,
            "mô tả": 0.45, "tiêu đề": 0.4,
        }[part.field]
        return {
            "field": part.field, "excerpt": excerpt,
            "processor": part.processor or ("user" if part.field == "ghi chú" else "metadata"),
            "processor_version": part.processor_version,
            "confidence": score, "evidence_type": "exact_phrase",
        }
    return None


def _snapshot(row):
    if row is None:
        return None
    return {name: getattr(row, name) for name in FIELDS}


def _signed_receipt(item, kind, group_id, version, before, evidence_key):
    return signing.dumps({
        "schema": 1, "owner": str(item.owner_id), "item": str(item.pk),
        "kind": kind, "group": group_id, "source_version": version,
        "before": before, "proof": evidence_key,
    }, salt=SALT, compress=True)


def _unpack(owner_id, item_id, token):
    if not isinstance(token, str) or not 1 <= len(token) <= 8192:
        raise ReviewError("review_receipt_invalid", 422)
    try:
        data = signing.loads(token, salt=SALT, max_age=RECEIPT_TTL)
    except signing.BadSignature:
        raise ReviewError("review_receipt_invalid_or_expired", 422) from None
    if (
        not isinstance(data, dict) or data.get("schema") != 1
        or data.get("owner") != str(owner_id) or data.get("item") != str(item_id)
        or data.get("kind") not in GROUPS or type(data.get("group")) is not int
        or data["group"] < 1 or not isinstance(data.get("source_version"), str)
        or not isinstance(data.get("proof"), str)
        or (data.get("before") is not None and (
            not isinstance(data["before"], dict)
            or set(data["before"]) != set(FIELDS)
        ))
    ):
        raise ReviewError("review_receipt_scope_mismatch", 422)
    return data


def _dismiss_key(data):
    return _hash([data["owner"], data["item"], data["source_version"],
                  data["kind"], data["group"], data["proof"]])


def _dismissals(session):
    stored = session.get(REJECT_SESSION_KEY, []) if session is not None else []
    return stored if isinstance(stored, list) else []


def _store_dismissals(session, keys):
    if session is None:
        raise ReviewError("review_session_required", 422)
    session[REJECT_SESSION_KEY] = keys[-MAX_SESSION_DISMISSALS:]
    if hasattr(session, "modified"):
        session.modified = True


def _owned_item(owner_id, item_id, *, lock=False):
    items = Item.objects.select_for_update() if lock else Item.objects
    item = items.filter(pk=item_id, owner_id=owner_id, deleted_at__isnull=True).first()
    if item is None:
        raise ReviewError("review_item_unavailable", 404)
    return item


def _build(item, session=None):
    parts = _parts(item)
    version = _version(item, parts)
    rules = GroupEvidence.from_texts(item.note, tuple(part.text for part in parts))
    has_body = any(p.field in ("ghi chú", "nội dung trích xuất") for p in parts)
    evidence_status = ("missing_text" if not parts else
                       "metadata_only" if not has_body else "available")
    rejected = set(_dismissals(session))
    proposed = []
    current = []
    excluded_topics = set(ItemTopicExclusion.objects.filter(item=item).values_list("topic_id", flat=True))
    for kind, (model, assignment_model) in GROUPS.items():
        visible = model.objects.filter(owner_id=item.owner_id)
        if kind != "tag":
            visible = visible.filter(archived=False)
        catalog = list(visible.values_list("pk", "name").order_by("name", "pk"))
        counts = Counter(normalize_phrase(name) for _, name in catalog)
        assignments = {
            getattr(row, kind + "_id"): row
            for row in assignment_model.objects.filter(
                item=item, **{kind + "__owner_id": item.owner_id}
            ).select_related(kind)
        }
        for row in assignments.values():
            group = getattr(row, kind)
            current.append({
                "kind": kind, "group_id": group.pk, "group_name": group.name,
                "origin": row.origin, "user_pinned": row.user_pinned,
                "confidence": row.confidence, "method_version": row.method_version,
                "source_version": row.source_version,
                "receipt": "" if row.user_pinned else _signed_receipt(
                    item, kind, group.pk, version, _snapshot(row), ""
                ),
            })
        for group_id, group_name in catalog:
            if kind == "topic" and group_id in excluded_topics:
                continue
            phrase = normalize_phrase(group_name)
            if not phrase or counts[phrase] != 1:
                continue  # Ambiguous taxonomy names must not be guessed.
            match = _match(kind, phrase, item.note, parts, rules)
            if match is None:
                continue
            proof = _hash([version, kind, group_id, match])
            if group_id in assignments:
                continue
            receipt_data = {
                "kind": kind, "group_id": group_id, "group_name": group_name,
                **match, "method_version": METHOD, "source_version": version,
                "proof": proof,
                "receipt": _signed_receipt(item, kind, group_id, version, None, proof),
            }
            if _dismiss_key({
                "owner": str(item.owner_id), "item": str(item.pk),
                "source_version": version, "kind": kind, "group": group_id, "proof": proof
            }) not in rejected:
                proposed.append(receipt_data)
    return {
        "item_id": str(item.pk), "source_version": version,
        "evidence_status": evidence_status, "current": current,
        "proposals": proposed, "counts": {
            "current": len(current), "proposed": len(proposed),
        }, "reject_persistence": "session_only",
        "confidence_note": "Điểm quy tắc, không phải xác suất đã hiệu chuẩn.",
    }


def review(owner_id, item_id, session=None):
    return _build(_owned_item(owner_id, item_id), session)


def queue(owner_id, *, limit=25, offset=0):
    """Bounded stable page for a 10k+ item inbox; detailed evidence loads per item."""
    if not isinstance(limit, int) or not 1 <= limit <= 100 or not isinstance(offset, int) or not 0 <= offset <= 1_000_000:
        raise ReviewError("review_invalid_page", 422)
    items = list(
        Item.objects.filter(owner_id=owner_id, deleted_at__isnull=True)
        .order_by("-saved_at", "pk")[offset:offset + limit + 1]
    )
    return {
        "results": [{
            "item_id": str(item.pk), "title": item.title or "(Không có tiêu đề)",
            "classification_status": item.classification_status,
        } for item in items[:limit]],
        "next_offset": offset + limit if len(items) > limit else None,
    }


def _after(action, before, version):
    if action == "accept":
        return {
            "origin": Assignment.Origin.USER, "user_pinned": False,
            "confidence": None, "method_version": ACCEPTED_METHOD,
            "source_version": version,
        }
    if before is None:
        return {
            "origin": Assignment.Origin.USER, "user_pinned": True,
            "confidence": None, "method_version": ACCEPTED_METHOD,
            "source_version": version,
        }
    return {**before, "origin": Assignment.Origin.USER, "user_pinned": True}


def _undo_receipt(data, action, after):
    return signing.dumps({
        **data, "undo_action": action, "after": after,
    }, salt=SALT, compress=True)


@transaction.atomic
def decide(owner_id, item_id, receipt, action, session=None):
    if action not in ("accept", "pin", "reject"):
        raise ReviewError("review_invalid_action", 422)
    data = _unpack(owner_id, item_id, receipt)
    get_user_model().objects.select_for_update(no_key=True).only("pk").get(pk=owner_id)
    item = _owned_item(owner_id, item_id, lock=True)
    before = data["before"]
    if _version(item, _parts(item)) != data["source_version"]:
        raise ReviewError("review_source_changed")
    kind = data["kind"]
    model, assignment_model = GROUPS[kind]
    if not model.objects.filter(pk=data["group"], owner_id=owner_id).exists():
        raise ReviewError("review_group_unavailable")
    query = assignment_model.objects.select_for_update().filter(
        item=item, **{kind + "_id": data["group"]}
    )
    row = query.first()
    current = _snapshot(row)
    if action == "reject":
        if before is not None or current is not None or not data["proof"]:
            raise ReviewError("review_reject_requires_proposal", 422)
    if action == "accept" and (before is not None or not data["proof"]):
        raise ReviewError("review_accept_requires_proposal", 422)
    # Re-check evidence after locking, including the rule and taxonomy.
    page = _build(item)
    actual = next((
        candidate for candidate in page["proposals"]
        if candidate["kind"] == kind and candidate["group_id"] == data["group"]
    ), None)
    if data["proof"] and actual is not None and data["proof"] != actual["proof"]:
        raise ReviewError("review_evidence_changed")
    if data["proof"] and actual is None and current == before:
        raise ReviewError("review_evidence_changed")
    if action == "reject":
        key = _dismiss_key(data)
        keys = _dismissals(session)
        if key not in keys:
            _store_dismissals(session, [*keys, key])
        return {"state": "rejected", "writes": 0, "idempotent": key in keys,
                "undo_receipt": _undo_receipt(data, "reject", None)}
    after = _after(action, before, data["source_version"])
    undo_receipt = _undo_receipt(data, action, after)
    if current == after:
        return {"state": "accepted" if action == "accept" else "pinned",
                "writes": 0, "idempotent": True, "undo_receipt": undo_receipt}
    if current != before:
        raise ReviewError("review_assignment_changed")
    # Existing user-curated or pinned assignments must never be overwritten.
    if row is not None and (row.origin == Assignment.Origin.USER or row.user_pinned):
        if action != "pin" or row.user_pinned:
            raise ReviewError("review_curated_protected")
    if row is None:
        assignment_model.objects.create(
            item=item, **{kind + "_id": data["group"]}, **after
        )
    else:
        for field, value in after.items():
            setattr(row, field, value)
        row.save(update_fields=list(after))
    return {"state": "accepted" if action == "accept" else "pinned",
            "writes": 1, "idempotent": False, "undo_receipt": undo_receipt}


@transaction.atomic
def undo(owner_id, item_id, receipt, session=None):
    data = _unpack(owner_id, item_id, receipt)
    if data.get("undo_action") not in ("accept", "pin", "reject"):
        raise ReviewError("review_undo_receipt_invalid", 422)
    if "after" not in data:
        raise ReviewError("review_undo_receipt_invalid", 422)
    get_user_model().objects.select_for_update(no_key=True).only("pk").get(pk=owner_id)
    item = _owned_item(owner_id, item_id, lock=True)
    if _version(item, _parts(item)) != data["source_version"]:
        raise ReviewError("review_source_changed")
    if data["undo_action"] == "reject":
        key = _dismiss_key(data)
        keys = _dismissals(session)
        present = key in keys
        if present:
            _store_dismissals(session, [value for value in keys if value != key])
        return {"state": "undone", "writes": 0, "idempotent": not present}
    kind = data["kind"]
    _, assignment_model = GROUPS[kind]
    row = assignment_model.objects.select_for_update().filter(
        item=item, **{kind + "_id": data["group"]}
    ).first()
    current = _snapshot(row)
    if current == data["before"]:
        return {"state": "undone", "writes": 0, "idempotent": True}
    if current != data["after"]:
        raise ReviewError("review_undo_conflict")
    if data["before"] is None:
        row.delete()
    else:
        for field, value in data["before"].items():
            setattr(row, field, value)
        row.save(update_fields=list(data["before"]))
    return {"state": "undone", "writes": 1, "idempotent": False}
