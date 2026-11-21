"""P02 / KT127: bounded, owner-scoped Markdown vault (not a database backup).

Only Markdown and portable metadata travel in the archive. No Drive file ID,
OAuth credential, signed URL, remote media fetch, or background job is emitted.
The router and UI deliberately remain unmounted until G00 integrates them.
"""

from __future__ import annotations

import hashlib
import io
import json
import posixpath
import re
import stat
import unicodedata
import zipfile
from datetime import datetime
from urllib.parse import quote, unquote, urlsplit
from uuid import UUID

from django.contrib.auth import get_user_model
from django.core import signing
from django.db import transaction
from django.utils import timezone
from ingestion.models import CaptureEvent
from storage.models import Asset

from .models import Item, ItemTopic, Source, Topic

FORMAT = "kt-markdown-vault"
VERSION = 1
MANIFEST = "vault-manifest.json"
SALT = "kt-p02-vault-preview-v1"
MAX_ZIP = 32 * 1024 * 1024
MAX_EXPANDED = 64 * 1024 * 1024
MAX_MANIFEST = 16 * 1024 * 1024
MAX_NOTE_FILE = 2 * 1024 * 1024
MAX_FILES = 10002
MAX_ITEMS = 10000
MAX_TOPICS = 5000
MAX_DEPTH = 64
MAX_EVENTS = 50000
MAX_ASSETS = 20000
SENSITIVE = re.compile(
    r"(?:access[_-]?token|refresh[_-]?token|client[_-]?secret|api[_-]?key|"
    r"authorization|cookie|password|private[_-]?key|session[_-]?token|"
    r"drive[_-]?file[_-]?id|x-goog-signature|x-amz-signature|signature|signed_url)"
    r"\s*(?:=|:)", re.IGNORECASE,
)
INTERNAL = re.compile(r"^#/muc/([0-9a-fA-F-]{36})$")
LINK = re.compile(r"(?<!!)(?<!\\)\[([^\]\n]+)\]\(([^)\n]+)\)")
ITEM_FIELDS = (
    "id", "kind", "title", "description", "saved_at", "published_at",
    "updated_at", "deleted_at", "favorite", "user_edit_version",
    "classification_status", "source_fetch", "asset_storage", "content_extract",
    "home_topic_id", "parent_item_id", "outline_order", "structure_version",
    "structure_origin",
)
TOPIC_FIELDS = ("id", "name", "parent_id", "archived", "node_kind", "sort_order")
ASSIGN_FIELDS = (
    "item_id", "topic_id", "origin", "user_pinned", "confidence",
    "method_version", "source_version",
)
SOURCE_FIELDS = (
    "item_id", "original_url", "canonical_url", "identity_hash", "platform",
    "platform_id", "captured_at", "published_at",
)
ASSET_FIELDS = (
    "id", "item_id", "role", "mime", "size", "sha256", "original_filename",
    "content_version",
)
EVENT_FIELDS = (
    "id", "item_id", "source_channel", "raw_kind", "raw_text", "original_url",
    "server_received_at", "client_sent_at", "status",
)
SECTIONS = ("items", "topics", "item_topics", "sources", "assets", "events")


class VaultError(ValueError):
    """Stable public validation codes; never return private archive contents."""


def digest(data: bytes | str) -> str:
    return hashlib.sha256(data.encode("utf-8") if isinstance(data, str) else data).hexdigest()


def _json_default(value):
    if isinstance(value, (datetime, UUID)):
        return value.isoformat() if isinstance(value, datetime) else str(value)
    raise TypeError(type(value).__name__)


def _json(value) -> bytes:
    return json.dumps(
        value, default=_json_default, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def _plain(value):
    return json.loads(_json(value))


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise VaultError("duplicate_manifest_key")
        result[key] = value
    return result


def _uuid(value):
    if not isinstance(value, str):
        raise VaultError("invalid_uuid")
    try:
        ident = UUID(value)
    except ValueError:
        raise VaultError("invalid_uuid") from None
    if str(ident) != value:
        raise VaultError("noncanonical_uuid")
    return value


def _timestamp(value, nullable=False):
    if value is None and nullable:
        return None
    if not isinstance(value, str):
        raise VaultError("invalid_timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise VaultError("invalid_timestamp") from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise VaultError("timezone_required")
    return parsed


def _safe_text(value, maximum):
    if not isinstance(value, str) or len(value) > maximum or "\x00" in value:
        raise VaultError("invalid_vault_text")
    try:
        value.encode("utf-8")
    except UnicodeError:
        raise VaultError("invalid_vault_text") from None
    return value


def _safe_url(value, optional=False):
    if not value and optional:
        return
    _safe_text(value, 4096)
    try:
        url = urlsplit(value)
        valid = url.scheme in ("https", "http") and url.hostname and not (
            url.username or url.password
        )
    except ValueError:
        valid = False
    if not valid or SENSITIVE.search(value) or re.search(r"(?i)(?:[?&#])(?:token|key|secret|sig|credential|password|auth|code)=", value):
        raise VaultError("unsafe_source_reference")


def _safe_path(path):
    if (
        not isinstance(path, str) or not 0 < len(path) <= 512
        or unicodedata.normalize("NFC", path) != path
        or path.startswith("/") or "\\" in path or ":" in path or "\x00" in path
    ):
        raise VaultError("unsafe_archive_path")
    if any(part in ("", ".", "..") for part in path.split("/")):
        raise VaultError("unsafe_archive_path")
    decoded = unquote(path)
    if decoded != path and (
        "\\" in decoded or decoded.startswith("/")
        or any(part in ("", ".", "..") for part in decoded.split("/"))
    ):
        raise VaultError("unsafe_archive_path")
    if any(ord(char) < 32 for char in path):
        raise VaultError("unsafe_archive_path")
    return path


def _slug(name):
    name = unicodedata.normalize("NFC", name)
    name = re.sub(r'[\x00-\x1f<>:"/\\|?*%]', "-", name)
    name = re.sub(r"\s+", " ", name).strip(". ")[:60] or "Untitled"
    if name.split(".")[0].upper() in {
        "CON", "PRN", "NUL", "AUX", *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }:
        name = "_" + name
    return name


def _links(text, resolver):
    """Convert simple inline Markdown links, but never fenced/indented/code HTML."""
    fence = None
    output = []
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(\`{3,}|~{3,})", line)
        if marker:
            if fence is None:
                fence = marker.group(1)
            elif marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence):
                fence = None
            output.append(line)
            continue
        if fence or re.match(r"^( {4}|\t|\s*<)", line):
            output.append(line)
            continue
        inline = list(re.finditer(r"(\`+).*?\1", line))

        def replace(match):
            if any(span.start() <= match.start() < span.end() for span in inline):
                return match.group(0)
            rewritten = resolver(match.group(2))
            return (
                match.group(0) if rewritten is None
                else "[" + match.group(1) + "](" + rewritten + ")"
            )

        output.append(LINK.sub(replace, line))
    return "".join(output)


def _front(row, sources):
    fields = {
        "item_id": row["id"], "version": row["user_edit_version"],
        "saved_at": row["saved_at"], "published_at": row["published_at"],
        "source_reference": [
            source["original_url"] for source in sources
            if source["item_id"] == row["id"]
        ],
    }
    return "---\n" + "".join(
        key + ": " + json.dumps(value, ensure_ascii=False) + "\n"
        for key, value in fields.items()
    ) + "---\n"


def _unfront(text):
    if not text.startswith("---\n"):
        raise VaultError("missing_vault_frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise VaultError("invalid_vault_frontmatter")
    front = {}
    for line in text[4:end].split("\n"):
        key, separator, value = line.partition(":")
        if not separator or key in front:
            raise VaultError("invalid_vault_frontmatter")
        try:
            front[key] = json.loads(value.strip(), object_pairs_hook=_unique_pairs)
        except (ValueError, RecursionError):
            raise VaultError("invalid_vault_frontmatter") from None
    return front, text[end + 5:]


def _check_tree(rows, parent_key, depth_limit=MAX_DEPTH):
    parents = {str(row["id"]): str(row[parent_key]) if row[parent_key] is not None else None for row in rows}
    if len(parents) != len(rows):
        raise VaultError("duplicate_vault_identity")
    for key in parents:
        depth, seen, current = 0, set(), key
        while current is not None:
            if current not in parents or current in seen or depth >= depth_limit:
                raise VaultError("invalid_vault_hierarchy")
            seen.add(current)
            current = parents[current]
            depth += 1


def _validate(data):
    if (
        not isinstance(data, dict)
        or data.get("format") != FORMAT or data.get("schema_version") != VERSION
        or data.get("media_included") is not False
        or any(not isinstance(data.get(key), list) for key in SECTIONS)
        or set(data) != {*SECTIONS, "format", "schema_version", "media_included", "created_at"}
    ):
        raise VaultError("unsupported_vault_format")
    _timestamp(data["created_at"])
    if (
        len(data["items"]) > MAX_ITEMS or len(data["topics"]) > MAX_TOPICS
        or len(data["assets"]) > MAX_ASSETS or len(data["events"]) > MAX_EVENTS
        or len(data["item_topics"]) > MAX_ITEMS * 20
        or len(data["sources"]) > MAX_ITEMS * 20
    ):
        raise VaultError("vault_collection_limit")
    ids = set()
    for row in data["items"]:
        if not isinstance(row, dict):
            raise VaultError("invalid_item")
        key = _uuid(row.get("id"))
        if key in ids:
            raise VaultError("duplicate_vault_identity")
        ids.add(key)
        if row.get("kind") not in Item.Kind.values:
            raise VaultError("invalid_item_kind")
        for field, limit in (("title", 512), ("description", 20000), ("_note", 100000)):
            _safe_text(row.get(field), limit)
        for field in ("saved_at", "updated_at"):
            _timestamp(row.get(field))
        for field in ("published_at", "deleted_at"):
            _timestamp(row.get(field), nullable=True)
        for field in ("user_edit_version", "structure_version", "outline_order"):
            if type(row.get(field)) is not int or not 0 <= row[field] <= 2**31 - 1:
                raise VaultError("invalid_item_version")
        for field in ("favorite",):
            if type(row.get(field)) is not bool:
                raise VaultError("invalid_item_flag")
        if row.get("parent_item_id") is not None:
            _uuid(row["parent_item_id"])
        if row.get("home_topic_id") is not None and type(row["home_topic_id"]) is not int:
            raise VaultError("invalid_home_topic")
        for field, limit in (("classification_status", 24), ("source_fetch", 16),
                             ("asset_storage", 16), ("content_extract", 16),
                             ("structure_origin", 12)):
            _safe_text(row.get(field), limit)
    _check_tree(data["items"], "parent_item_id")
    folder_ids = set()
    for row in data["topics"]:
        if not isinstance(row, dict) or type(row.get("id")) is not int or row["id"] < 1:
            raise VaultError("invalid_folder")
        folder_ids.add(row["id"])
        _safe_text(row.get("name"), 120)
        if not row["name"].strip() or row.get("node_kind") not in Topic.Kind.values:
            raise VaultError("invalid_folder")
        if row.get("parent_id") is not None and type(row["parent_id"]) is not int:
            raise VaultError("invalid_folder")
        if (type(row.get("archived")) is not bool or type(row.get("sort_order")) is not int
                or row["sort_order"] < 0 or row["sort_order"] > 2**31 - 1):
            raise VaultError("invalid_folder")
    if len(folder_ids) != len(data["topics"]):
        raise VaultError("duplicate_vault_identity")
    _check_tree(data["topics"], "parent_id")
    for row in data["items"]:
        if row["home_topic_id"] is not None and row["home_topic_id"] not in folder_ids:
            raise VaultError("invalid_home_topic")
    assigned = set()
    for row in data["item_topics"]:
        pair = (row.get("item_id"), row.get("topic_id"))
        if pair in assigned or pair[0] not in ids or pair[1] not in folder_ids:
            raise VaultError("invalid_item_membership")
        assigned.add(pair)
        if row.get("origin") not in ("user", "auto") or type(row.get("user_pinned")) is not bool:
            raise VaultError("invalid_item_membership")
        _safe_text(row.get("method_version"), 64)
        _safe_text(row.get("source_version"), 128)
        if row.get("confidence") is not None and (
            type(row["confidence"]) not in (int, float)
            or not 0 <= row["confidence"] <= 1
        ):
            raise VaultError("invalid_item_membership")
    for row in data["sources"]:
        if row.get("item_id") not in ids:
            raise VaultError("unresolved_item")
        _safe_url(row.get("original_url"))
        _safe_url(row.get("canonical_url"))
        _timestamp(row.get("captured_at"))
        _timestamp(row.get("published_at"), nullable=True)
        for field, limit in (("identity_hash", 64), ("platform", 24), ("platform_id", 255)):
            _safe_text(row.get(field), limit)
    assets = set()
    for row in data["assets"]:
        key = _uuid(row.get("id"))
        if key in assets or row.get("item_id") not in ids:
            raise VaultError("invalid_asset")
        assets.add(key)
        _safe_text(row.get("original_filename"), 255)
        _safe_text(row.get("mime"), 255)
        _safe_text(row.get("sha256"), 64)
        if row["sha256"] and not re.fullmatch("[a-fA-F0-9]{64}", row["sha256"]):
            raise VaultError("invalid_asset_digest")
        if row.get("size") is not None and (
            type(row["size"]) is not int or not 0 <= row["size"] <= 2**63-1
        ):
            raise VaultError("invalid_asset")
        if (type(row.get("content_version")) is not int
                or not 1 <= row["content_version"] <= 2**31 - 1):
            raise VaultError("invalid_asset")
        _safe_text(row.get("role"), 24)
    events = set()
    for row in data["events"]:
        key = _uuid(row.get("id"))
        if key in events or row.get("item_id") not in ids:
            raise VaultError("invalid_capture_history")
        events.add(key)
        if row.get("raw_kind") not in ("text", "link"):
            raise VaultError("invalid_capture_history")
        _safe_text(row.get("raw_text"), 100000)
        _safe_text(row.get("source_channel"), 32)
        _safe_text(row.get("status"), 24)
        _safe_text(row.get("original_url"), 4096)
        if row["raw_kind"] == "link":
            _safe_url(row["original_url"])
        elif row["original_url"] or not row["raw_text"]:
            raise VaultError("invalid_capture_history")
        _timestamp(row.get("server_received_at"))
        _timestamp(row.get("client_sent_at"), nullable=True)
    if SENSITIVE.search(_json(data).decode("utf-8")):
        raise VaultError("sensitive_input_blocked")


@transaction.atomic
def export_vault(owner) -> bytes:
    """Export one canonical .md per Item; aliases and structure stay in manifest."""
    get_user_model().objects.select_for_update().get(pk=owner.pk)
    notes = list(Item.objects.filter(owner=owner).order_by("pk").values(*ITEM_FIELDS, "note")[:MAX_ITEMS+1])
    if len(notes) > MAX_ITEMS:
        raise VaultError("vault_item_limit")
    ids = [row["id"] for row in notes]
    topics = _plain(list(Topic.objects.filter(owner=owner).order_by("id").values(*TOPIC_FIELDS)))
    placements = _plain(list(ItemTopic.objects.filter(item_id__in=ids, topic__owner=owner).order_by("item_id", "topic_id").values(*ASSIGN_FIELDS)))
    # Source.metadata is uncontrolled extractor JSON and may carry cookies or
    # provider identifiers. Portable format exports only allowlisted safe fields.
    sources = _plain(list(Source.objects.filter(item_id__in=ids).order_by("item_id", "id").values(*SOURCE_FIELDS)))
    assets = _plain(list(Asset.objects.filter(item_id__in=ids).order_by("item_id", "id").values(*ASSET_FIELDS)))
    events = _plain(list(CaptureEvent.objects.filter(owner=owner, item_id__in=ids).order_by("item_id", "id").values(*EVENT_FIELDS)))
    folders = {row["id"]: row for row in topics}
    paths = {}

    def folder_path(key, seen=()):
        if key is None:
            return "Notes"
        if key in seen or len(seen) >= MAX_DEPTH or key not in folders:
            raise VaultError("invalid_vault_hierarchy")
        row = folders[key]
        return folder_path(row["parent_id"], (*seen, key)) + "/" + _slug(row["name"]) + "--t" + str(key)

    for row in notes:
        path = folder_path(row["home_topic_id"]) + "/" + _slug(row["title"]) + "--" + str(row["id"]) + ".md"
        paths[str(row["id"])] = _safe_path(path)
    files = {}
    items = []
    for row in notes:
        row = _plain(row)
        original = row.pop("note")
        mappings = {}
        current = paths[row["id"]]

        def to_portable(destination):
            match = INTERNAL.fullmatch(destination)
            if match is None:
                return None
            try:
                target = str(UUID(match.group(1)))
            except ValueError:
                return None
            if target not in paths:
                return None
            relative = quote(
                posixpath.relpath(paths[target], posixpath.dirname(current)),
                safe="/._-",
            )
            mappings[relative] = destination
            return relative

        body = _links(original, to_portable)
        contents = (_front(row, sources) + body).encode("utf-8")
        if len(contents) > MAX_NOTE_FILE:
            raise VaultError("vault_note_limit")
        files[current] = contents
        items.append({
            **row, "path": current, "file_sha256": digest(contents),
            "note_sha256": digest(original), "link_mapping": mappings,
        })
    manifest = {
        "format": FORMAT, "schema_version": VERSION, "media_included": False,
        "created_at": timezone.now().isoformat(), "items": items,
        "topics": topics, "item_topics": placements, "sources": sources,
        "assets": assets, "events": events,
    }
    _check_sensitive = _json(manifest)
    if SENSITIVE.search(_check_sensitive.decode("utf-8")) or any(
        SENSITIVE.search(value.decode("utf-8")) for value in files.values()
    ):
        raise VaultError("sensitive_input_blocked")
    if len(_check_sensitive) > MAX_MANIFEST:
        raise VaultError("vault_manifest_limit")
    if sum(len(v) for v in files.values()) + len(_check_sensitive) > MAX_EXPANDED:
        raise VaultError("vault_expanded_limit")
    buff = io.BytesIO()
    with zipfile.ZipFile(buff, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as writer:
        writer.writestr(MANIFEST, _check_sensitive)
        for path, raw in sorted(files.items()):
            writer.writestr(path, raw)
    result = buff.getvalue()
    if len(result) > MAX_ZIP:
        raise VaultError("vault_archive_limit")
    return result


def parse_vault(archive: bytes):
    """Strict bounded parser. Edited Markdown bodies are previewed, not auto-applied."""
    if not isinstance(archive, bytes) or len(archive) > MAX_ZIP:
        raise VaultError("vault_archive_limit")
    files = {}
    folded = set()
    expanded = 0
    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as reader:
            infos = reader.infolist()
            if len(infos) > MAX_FILES:
                raise VaultError("vault_file_limit")
            for info in infos:
                path = _safe_path(info.filename)
                normalized = path.casefold()
                if (
                    info.is_dir() or normalized in folded or info.flag_bits & 1
                    or stat.S_ISLNK(info.external_attr >> 16)
                    or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                ):
                    raise VaultError("unsafe_archive_entry")
                folded.add(normalized)
                limit = MAX_MANIFEST if path == MANIFEST else MAX_NOTE_FILE
                expanded += info.file_size
                if (
                    info.file_size > limit or expanded > MAX_EXPANDED
                    or (info.file_size > 1024*1024
                        and info.file_size > 200 * max(info.compress_size, 1))
                ):
                    raise VaultError("zip_bomb_or_file_limit")
                files[path] = reader.read(info)
    except (zipfile.BadZipFile, zipfile.LargeZipFile, RuntimeError, OSError, EOFError):
        raise VaultError("invalid_vault_archive") from None
    if MANIFEST not in files:
        raise VaultError("unsupported_plain_markdown_vault")
    try:
        data = json.loads(files.pop(MANIFEST).decode("utf-8"), object_pairs_hook=_unique_pairs)
    except (ValueError, UnicodeError, RecursionError):
        raise VaultError("invalid_vault_manifest") from None
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise VaultError("invalid_vault_manifest")
    if len(data["items"]) > MAX_ITEMS:
        raise VaultError("vault_item_limit")
    expected = set()
    for row in data["items"]:
        if not isinstance(row, dict):
            raise VaultError("invalid_item")
        path = _safe_path(row.get("path"))
        if path in expected or path not in files:
            raise VaultError("missing_or_duplicate_note")
        expected.add(path)
        try:
            front, body = _unfront(files[path].decode("utf-8"))
        except UnicodeError:
            raise VaultError("vault_markdown_not_utf8") from None
        if (
            front.get("item_id") != row.get("id")
            or front.get("version") != row.get("user_edit_version")
            or front.get("saved_at") != row.get("saved_at")
            or front.get("published_at") != row.get("published_at")
        ):
            raise VaultError("frontmatter_identity_conflict")
        mapping = row.get("link_mapping")
        if not isinstance(mapping, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            or INTERNAL.fullmatch(value) is None for key, value in mapping.items()
        ):
            raise VaultError("invalid_link_mapping")
        row["_note"] = _links(body, lambda destination: mapping.get(destination))
        row["_edited"] = digest(files[path]) != row.get("file_sha256")
        if not row["_edited"] and digest(row["_note"]) != row.get("note_sha256"):
            raise VaultError("vault_note_hash_mismatch")
    if set(files) != expected:
        raise VaultError("unexpected_vault_entry")
    try:
        _validate(data)
    except (KeyError, TypeError, AttributeError, IndexError, OverflowError, RecursionError) as error:
        raise VaultError("invalid_vault_manifest") from error
    return data, digest(archive)


def _fingerprint(owner, ids):
    """Detect changes between preview and apply, without exposing local content."""
    owned = Item.objects.filter(owner=owner, pk__in=ids)
    rows = list(owned.order_by("pk").values(
        "id", "kind", "note", "title", "description", "saved_at",
        "updated_at", "deleted_at", "user_edit_version", "structure_version",
        "home_topic_id", "parent_item_id",
    ))
    relations = list(ItemTopic.objects.filter(item__owner=owner, item_id__in=ids).order_by("item_id", "topic_id").values_list("item_id", "topic_id", "user_pinned"))
    return digest(_json({"items": rows, "relations": relations}))


def _statuses(owner, data):
    imported = data["items"]
    existing = Item.objects.filter(pk__in=[row["id"] for row in imported]).in_bulk()
    output = []
    for row in imported:
        local = existing.get(UUID(row["id"]))
        reason = ""
        if local is None:
            status = "new"
        elif local.owner_id != owner.pk:
            status, reason = "conflict", "identity_not_available"
        elif local.kind != row["kind"] or local.saved_at != _timestamp(row["saved_at"]):
            status, reason = "conflict", "immutable_identity_changed"
        elif (
            local.user_edit_version > row["user_edit_version"]
            or local.structure_version > row["structure_version"]
        ):
            status, reason = "conflict", "local_version_newer"
        elif (
            local.title == row["title"] and local.note == row["_note"]
            and local.description == row["description"]
            and local.user_edit_version == row["user_edit_version"]
            and local.structure_version == row["structure_version"]
            and str(local.parent_item_id or "") == str(row["parent_item_id"] or "")
            and local.deleted_at == _timestamp(row["deleted_at"], nullable=True)
        ):
            status = "unchanged"
        else:
            status = "update"
        output.append({
            "item_id": row["id"], "title": row["title"], "status": status,
            "reason": reason, "edited_markdown": row["_edited"],
            "version": row["user_edit_version"],
            "before": local.note[:320] if local is not None and local.owner_id == owner.pk else None,
            "after": row["_note"][:320],
        })
    return output


def preview_import(owner, archive: bytes):
    data, zip_hash = parse_vault(archive)
    statuses = _statuses(owner, data)
    keys = [row["id"] for row in data["items"]]
    receipt = signing.dumps({
        "owner": str(owner.pk), "zip": zip_hash, "baseline": _fingerprint(owner, keys),
    }, salt=SALT, compress=True)
    return {
        "receipt": receipt, "rows": statuses[:200],
        "more_count": max(0, len(statuses) - 200),
        "counts": {name: sum(row["status"] == name for row in statuses)
                   for name in ("new", "update", "unchanged", "conflict")},
        "metadata": {name: len(data[name]) for name in SECTIONS},
        "media_missing": len(data["assets"]),
        "warnings": [
            "Không kèm media gốc, Drive ID hoặc khóa OAuth; asset chỉ là metadata chưa xác minh.",
            "Ghi chú đã sửa trong ZIP chỉ áp dụng sau bước duyệt; Markdown ngoài định dạng KT127 chưa hỗ trợ import.",
            "Không thay thế PostgreSQL/Google Drive backup. Kiểm tra dữ liệu nhạy cảm trước khi chia sẻ ZIP.",
        ],
    }


def _topics(owner, rows):
    mapping = {}
    pending = list(rows)
    while pending:
        later = []
        for row in pending:
            parent = row["parent_id"]
            if parent is not None and parent not in mapping:
                later.append(row)
                continue
            parent_id = mapping.get(parent)
            name = unicodedata.normalize("NFC", row["name"])
            existing = next(
                (node for node in Topic.objects.filter(owner=owner, parent_id=parent_id)
                 if unicodedata.normalize("NFC", node.name).casefold() == name.casefold()),
                None,
            )
            if existing is None:
                existing = Topic.objects.create(
                    owner=owner, name=name, parent_id=parent_id,
                    node_kind=row["node_kind"], archived=row["archived"],
                    sort_order=row["sort_order"],
                )
            mapping[row["id"]] = existing.pk
        if len(later) == len(pending):
            raise VaultError("invalid_vault_hierarchy")
        pending = later
    return mapping


def _selected_topic_rows(data, chosen, statuses):
    """Import only the folders needed by selected changed items and their ancestors.

    An unrelated archive folder must not be written when the user chooses a
    subset of notes. Folder placement is allowed to bring its parent chain.
    """
    affected = {row["id"] for row in data["items"]
                if row["id"] in chosen and statuses[row["id"]] != "unchanged"}
    wanted = {row["home_topic_id"] for row in data["items"]
              if row["id"] in affected and row["home_topic_id"] is not None}
    wanted.update(row["topic_id"] for row in data["item_topics"]
                  if row["item_id"] in affected)
    by_id = {row["id"]: row for row in data["topics"]}
    needed = set()
    for topic_id in wanted:
        while topic_id is not None and topic_id not in needed:
            if topic_id not in by_id:
                raise VaultError("invalid_item_membership")
            needed.add(topic_id)
            topic_id = by_id[topic_id]["parent_id"]
    return [row for row in data["topics"] if row["id"] in needed]


def _check_selection(owner, data, selected):
    if not isinstance(selected, list) or len(selected) > MAX_ITEMS or any(not isinstance(k, str) for k in selected):
        raise VaultError("invalid_vault_selection")
    statuses = {row["item_id"]: row["status"] for row in _statuses(owner, data)}
    chosen = set(statuses) if selected == ["*"] else set(selected)
    if not chosen <= statuses.keys():
        raise VaultError("invalid_vault_selection")
    if any(statuses[key] == "conflict" for key in chosen):
        raise VaultError("vault_import_conflict")
    available = {str(key) for key in Item.objects.filter(owner=owner, pk__in=statuses).values_list("pk", flat=True)}
    available |= chosen
    if any(
        row["parent_item_id"] not in available for row in data["items"]
        if row["id"] in chosen and row["parent_item_id"] is not None
    ):
        raise VaultError("selection_missing_parent")
    # Existing unrelated parent pointers can create a cross-archive cycle.
    parents = {
        str(pk): str(parent) if parent is not None else None
        for pk, parent in Item.objects.filter(owner=owner).values_list("pk", "parent_item_id")
    }
    for row in data["items"]:
        if row["id"] in chosen:
            parents[row["id"]] = row["parent_item_id"]
    for key in chosen:
        current, seen = key, set()
        while current is not None:
            if current in seen or len(seen) >= MAX_DEPTH or current not in parents:
                raise VaultError("invalid_vault_hierarchy")
            seen.add(current)
            current = parents[current]
    return chosen, statuses


@transaction.atomic
def apply_import(owner, archive: bytes, receipt: str, selected: list[str]):
    """Explicit selected changes only; no Drive calls, no generated CaptureEvents."""
    data, zip_hash = parse_vault(archive)
    try:
        token = signing.loads(receipt, salt=SALT, max_age=900)
    except signing.BadSignature:
        raise VaultError("invalid_or_expired_preview") from None
    if token.get("owner") != str(owner.pk) or token.get("zip") != zip_hash:
        raise VaultError("vault_preview_scope_mismatch")
    get_user_model().objects.select_for_update().get(pk=owner.pk)
    chosen, statuses = _check_selection(owner, data, selected)
    if not chosen or all(statuses[key] == "unchanged" for key in chosen):
        return {"state": "unchanged", "created": 0, "updated": 0,
                "events_created": 0, "assets_created": 0, "media_verified": 0}
    if token.get("baseline") != _fingerprint(owner, [row["id"] for row in data["items"]]):
        raise VaultError("vault_preview_database_changed")
    folders = _topics(owner, _selected_topic_rows(data, chosen, statuses))
    created = updated = events_created = assets_created = 0
    for row in data["items"]:
        key = row["id"]
        if key not in chosen or statuses[key] == "unchanged":
            continue
        values = {field: row[field] for field in ITEM_FIELDS
                  if field not in ("id", "parent_item_id", "home_topic_id")}
        values["note"] = row["_note"]
        values["published_at"] = _timestamp(row["published_at"], nullable=True)
        values["deleted_at"] = _timestamp(row["deleted_at"], nullable=True)
        values["saved_at"] = _timestamp(row["saved_at"])
        values["updated_at"] = _timestamp(row["updated_at"])
        if statuses[key] == "new":
            Item.objects.create(id=key, owner=owner, **values)
            Item.objects.filter(pk=key, owner=owner).update(
                saved_at=values["saved_at"], updated_at=values["updated_at"]
            )
            created += 1
        else:
            values.pop("saved_at")
            local = Item.objects.select_for_update().get(pk=key, owner=owner)
            if row["_edited"] or row["user_edit_version"] == local.user_edit_version:
                values["user_edit_version"] = max(
                    row["user_edit_version"], local.user_edit_version + 1
                )
                values["updated_at"] = timezone.now()
            Item.objects.filter(pk=key, owner=owner).update(**values)
            updated += 1
    for row in data["items"]:
        if row["id"] in chosen and statuses[row["id"]] != "unchanged":
            Item.objects.filter(pk=row["id"], owner=owner).update(
                parent_item_id=row["parent_item_id"],
                home_topic_id=folders.get(row["home_topic_id"]),
            )
    for row in data["item_topics"]:
        if row["item_id"] not in chosen or statuses[row["item_id"]] == "unchanged":
            continue
        ItemTopic.objects.get_or_create(
            item_id=row["item_id"], topic_id=folders[row["topic_id"]],
            defaults={field: row[field] for field in ASSIGN_FIELDS
                      if field not in ("item_id", "topic_id")},
        )
    for row in data["sources"]:
        if row["item_id"] not in chosen or statuses[row["item_id"]] == "unchanged":
            continue
        lookup = {name: row[name] for name in ("item_id", "identity_hash", "original_url", "canonical_url")}
        if not Source.objects.filter(**lookup).exists():
            Source.objects.create(
                **{name: _timestamp(row[name], nullable=(name == "published_at"))
                   if name in ("captured_at", "published_at") else row[name]
                   for name in SOURCE_FIELDS},
            )
    for row in data["assets"]:
        if row["item_id"] not in chosen:
            continue
        local = Asset.objects.filter(pk=row["id"]).select_related("item").first()
        if local is not None:
            if (
                local.item.owner_id != owner.pk or str(local.item_id) != row["item_id"]
                or local.sha256 != row["sha256"] or local.size != row["size"]
            ):
                raise VaultError("vault_asset_identity_conflict")
        elif statuses[row["item_id"]] != "unchanged":
            Asset.objects.create(**row)
            assets_created += 1
    for row in data["events"]:
        if row["item_id"] not in chosen:
            continue
        local = CaptureEvent.objects.filter(pk=row["id"]).first()
        if local is not None:
            if (
                local.owner_id != owner.pk or str(local.item_id) != row["item_id"]
                or local.raw_text != row["raw_text"]
                or local.original_url != row["original_url"]
                or local.server_received_at != _timestamp(row["server_received_at"])
            ):
                raise VaultError("vault_capture_identity_conflict")
        elif statuses[row["item_id"]] != "unchanged":
            values = {
                field: _timestamp(row[field], nullable=(field == "client_sent_at"))
                if field in ("server_received_at", "client_sent_at") else row[field]
                for field in EVENT_FIELDS
            }
            # Intentionally do not replay the original idempotency key.
            CaptureEvent.objects.create(owner=owner, idempotency_key=None, **values)
            events_created += 1
    return {
        "state": "imported", "created": created, "updated": updated,
        "events_created": events_created, "assets_created": assets_created,
        "media_verified": 0,
    }
