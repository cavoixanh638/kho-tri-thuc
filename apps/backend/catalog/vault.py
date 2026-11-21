"""Bounded portable Markdown snapshots. No media download or remote writes."""

import hashlib
import io
import json
import posixpath
import re
import stat
import unicodedata
import zipfile
from datetime import date, datetime
from urllib.parse import quote, unquote, urlsplit
from uuid import UUID, NAMESPACE_URL, uuid5

from django.contrib.auth import get_user_model
from django.core import signing
from django.db import IntegrityError, transaction
from django.db.models import Q
from ingestion.models import CaptureEvent
from jobs.repository import JobRepository
from processing.knowledge import SECRET
from processing.models import ClipAnnotation, DerivedContent
from storage.models import Asset, StorageLocation

from .collection_models import SavedCollection
from .collection_service import CollectionQuery
from .models import Item, ItemProject, ItemTag, ItemTopic, Project, Source, Tag, Topic

MAX_ARCHIVE = 32 * 1024 * 1024
MAX_EXPANDED = 64 * 1024 * 1024
MAX_FILE = 2 * 1024 * 1024
MAX_ITEMS = 10_000
SALT = "kt-portable-vault-v1"
ITEM_FIELDS = (
    "id", "kind", "title", "description", "saved_at", "published_at", "updated_at",
    "favorite", "deleted_at", "user_edit_version", "classification_status",
    "source_fetch", "asset_storage", "content_extract", "home_topic_id",
    "parent_item_id", "outline_order", "structure_version", "structure_origin",
)
GROUPS = {"topics": Topic, "projects": Project, "tags": Tag}
GROUP_FIELDS = {
    "topics": ("id", "name", "parent_id", "archived", "node_kind", "sort_order"),
    "projects": ("id", "name", "description", "archived"),
    "tags": ("id", "name"),
}
RELATIONS = {"item_topics": (ItemTopic, "topic"), "item_projects": (ItemProject, "project"), "item_tags": (ItemTag, "tag")}
RELATION_FIELDS = ("id", "item_id", "origin", "user_pinned", "confidence", "method_version", "source_version")
ROW_MODELS = {
    "sources": (Source, ("id", "item_id", "original_url", "canonical_url", "identity_hash", "platform", "platform_id", "captured_at", "published_at")),
    "assets": (Asset, ("id", "item_id", "role", "mime", "size", "sha256", "original_filename", "content_version")),
    "locations": (StorageLocation, ("id", "asset_id", "provider", "provider_file_id", "status", "verified_at", "provider_modified_at", "provider_revision")),
    "parts": (DerivedContent, ("id", "item_id", "asset_id", "kind", "text", "source_locator", "processor", "processor_version", "input_hash", "status", "created_at")),
    "events": (CaptureEvent, ("id", "item_id", "source_channel", "raw_kind", "raw_text", "original_url", "server_received_at", "client_sent_at", "idempotency_key", "status")),
    "clips": (ClipAnnotation, ("id", "item_id", "capture_id", "source_id", "part_id", "asset_id", "mode", "quote", "quote_hash", "source_version", "processor_version", "locator", "source_url", "page_title", "verification", "inserted_edit_version", "created_at")),
    "collections": (SavedCollection, ("id", "name", "normalized_name", "query", "view", "version", "created_at", "updated_at")),
}


class VaultError(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode("utf-8")).hexdigest()


def exact_default(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    raise TypeError(type(value).__name__)


def json_bytes(value):
    return json.dumps(value, default=exact_default, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def primitive(value):
    return json.loads(json_bytes(value))


def safe_name(name):
    name = unicodedata.normalize("NFC", name)
    name = re.sub(r'[\x00-\x1f<>:"/\\|?*#%]', "-", name)
    name = re.sub(r"\s+", "-", name).strip(". -")[:48] or "Untitled"
    return "_" + name if name.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))} else name


def safe_path(value):
    if not isinstance(value, str) or not value or "\\" in value or value.startswith(("/", ".")) or ":" in value:
        raise VaultError("unsafe_archive_path")
    if any(part in {"", ".", ".."} for part in value.rstrip("/").split("/")):
        raise VaultError("unsafe_archive_path")
    decoded = unquote(value)
    if decoded.startswith("/") or "\\" in decoded or ".." in decoded.split("/"):
        raise VaultError("unsafe_archive_path")
    return value


def rewrite_links(text, resolve):
    """Rewrite supported inline link destinations only, outside code/HTML."""
    fence, lines = None, []
    pattern = re.compile(r"(?<!!)(?<!\\)\[[^\[\]<>\\\n]*\]\(([^)\n]+)\)")
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            if fence is None:
                fence = marker[1]
            elif marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                fence = None
            lines.append(line)
            continue
        if fence or re.match(r"^( {4}|\t|\s*<)", line):
            lines.append(line)
            continue
        spans = list(re.finditer(r"(`+).*?\1", line))
        def replacement(match):
            if any(span.start() <= match.start() < span.end() for span in spans):
                return match[0]
            destination = resolve(match[1])
            return match[0] if destination is None else match[0][:match.start(1) - match.start()] + destination + match[0][match.end(1) - match.start():]
        lines.append(pattern.sub(replacement, line))
    return "".join(lines)


def check_url(value):
    if not value:
        return
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise VaultError("unsafe_source_reference")
    if re.search(r"(?:[?&#])(?:access_token|refresh_token|client_secret|signature|authorization|api_key)=", value, re.IGNORECASE):
        raise VaultError("unsafe_source_reference")


def tree_check(rows, parent_key, key="id"):
    parents = {str(row[key]): str(row[parent_key]) if row.get(parent_key) is not None else None for row in rows}
    if len(parents) != len(rows):
        raise VaultError("duplicate_identity")
    for child in parents:
        seen, cursor = set(), child
        while cursor is not None:
            if cursor in seen or cursor not in parents or len(seen) >= 65:
                raise VaultError("invalid_or_cyclic_hierarchy")
            seen.add(cursor)
            cursor = parents[cursor]


def source_rows(owner, items):
    ids = [item.pk for item in items]
    payload = {"items": primitive([{**{field: getattr(item, field) for field in ITEM_FIELDS}, "note": item.note} for item in items])}
    for name, model in GROUPS.items():
        payload[name] = primitive(list(model.objects.filter(owner=owner).order_by("id").values(*GROUP_FIELDS[name])))
    for name, (model, field) in RELATIONS.items():
        payload[name] = primitive(list(model.objects.filter(item_id__in=ids, **{field + "__owner": owner}).order_by("id").values(*RELATION_FIELDS, field + "_id")))
    for name, (model, fields) in ROW_MODELS.items():
        query = model.objects.filter(owner=owner) if name == "collections" else model.objects.filter(asset__item_id__in=ids) if name == "locations" else model.objects.filter(item_id__in=ids)
        if name == "events":
            query = query.filter(owner=owner)
        payload[name] = primitive(list(query.order_by("id").values(*fields)))
    return payload


@transaction.atomic
def export_vault(owner):
    get_user_model().objects.select_for_update().get(pk=owner.pk)
    items = list(Item.objects.filter(owner=owner).select_for_update().order_by("id")[:MAX_ITEMS + 1])
    if len(items) > MAX_ITEMS:
        raise VaultError("vault_item_limit")
    payload = source_rows(owner, items)
    validate_payload(payload)
    paths, folder_paths = {}, {}
    folders = {row["id"]: row for row in payload["topics"]}
    def folder_path(key):
        if key is None:
            return "Notes"
        if key not in folder_paths:
            row = folders[key]
            folder_paths[key] = folder_path(row["parent_id"]) + "/" + safe_name(row["name"]) + "--t" + str(key)
        return folder_paths[key]
    for key in folders:
        folder_path(key)
    for row in payload["items"]:
        paths[row["id"]] = folder_path(row["home_topic_id"]) + "/" + safe_name(row["title"] or row["note"].lstrip("# \r\n").split("\n")[0]) + "--" + row["id"] + ".md"
    files = {}
    for row in payload["items"]:
        raw = row.pop("note")
        current = paths[row["id"]]
        originals = {}
        def portable(destination):
            match = re.fullmatch(r"#/muc/([a-fA-F0-9-]{36})", destination)
            target = str(UUID(match[1])) if match else None
            if target not in paths:
                return None
            value = quote(posixpath.relpath(paths[target], posixpath.dirname(current)), safe="/.-_")
            originals[value] = destination
            return value
        body = rewrite_links(raw, portable)
        front = {"item_id": row["id"], "version": row["user_edit_version"], "saved_at": row["saved_at"], "published_at": row["published_at"], "source_reference": [source["original_url"] for source in payload["sources"] if source["item_id"] == row["id"]]}
        content = ("---\n" + "\n".join(key + ": " + json.dumps(value, ensure_ascii=False) for key, value in front.items()) + "\n---\n" + body).encode("utf-8")
        if len(content) > MAX_FILE:
            raise VaultError("vault_file_limit")
        row.update(path=current, file_sha256=digest(content), note_sha256=digest(raw), portable_links=originals)
        files[current] = content
    manifest = {"format": "kt-markdown-vault", "schema_version": 1, "media_included": False, "folders": folder_paths, "data": payload}
    manifest_bytes = json_bytes(manifest)
    if SECRET.search(manifest_bytes.decode()) or any(SECRET.search(data.decode("utf-8")) for data in files.values()):
        raise VaultError("sensitive_input_blocked")
    if sum(map(len, files.values())) + len(manifest_bytes) > MAX_EXPANDED:
        raise VaultError("vault_expanded_limit")
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for path in sorted(folder_paths.values()):
            output.writestr(path + "/", b"")
        output.writestr("vault-manifest.json", manifest_bytes)
        for path, content in sorted(files.items()):
            output.writestr(path, content)
    result = archive.getvalue()
    if len(result) > MAX_ARCHIVE:
        raise VaultError("vault_archive_limit")
    return result


def unique_json(pairs):
    data = {}
    for key, value in pairs:
        if key in data:
            raise VaultError("duplicate_json_key")
        data[key] = value
    return data


def split_frontmatter(text):
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        raise VaultError("invalid_frontmatter")
    values = {}
    for line in text[4:end].split("\n"):
        if not line.strip():
            continue
        key, sep, value = line.partition(":")
        if not sep or key in values:
            raise VaultError("invalid_frontmatter")
        try:
            values[key] = json.loads(value.strip())
        except ValueError:
            raise VaultError("only_json_valued_frontmatter_supported") from None
    return values, text[end + 5:]


def parse_vault(content, owner):
    if not isinstance(content, bytes) or len(content) > MAX_ARCHIVE:
        raise VaultError("vault_archive_limit")
    files, folded = {}, set()
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            entries = archive.infolist()
            if len(entries) > 20_000 or sum(row.file_size for row in entries) > MAX_EXPANDED:
                raise VaultError("vault_expanded_limit")
            for row in entries:
                safe_path(row.filename)
                normalized = unicodedata.normalize("NFC", row.filename).casefold()
                if normalized in folded or row.flag_bits & 1 or stat.S_ISLNK(row.external_attr >> 16):
                    raise VaultError("unsafe_or_duplicate_archive_entry")
                folded.add(normalized)
                if row.file_size > MAX_FILE and row.filename != "vault-manifest.json":
                    raise VaultError("vault_file_limit")
                if not row.is_dir():
                    files[row.filename] = archive.read(row)
    except (zipfile.BadZipFile, RuntimeError, OSError):
        raise VaultError("invalid_archive") from None
    if "vault-manifest.json" not in files:
        return parse_plain_markdown(files, owner), digest(content)
    try:
        manifest = json.loads(files.pop("vault-manifest.json").decode("utf-8"), object_pairs_hook=unique_json)
    except (UnicodeError, ValueError):
        raise VaultError("invalid_manifest") from None
    if manifest.get("format") != "kt-markdown-vault" or manifest.get("schema_version") != 1:
        raise VaultError("unknown_vault_version")
    payload = manifest.get("data")
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise VaultError("invalid_manifest")
    declared = set()
    for row in payload["items"]:
        path = safe_path(row.get("path"))
        if path in declared or path not in files or digest(files[path]) != row.get("file_sha256"):
            raise VaultError("markdown_hash_mismatch")
        declared.add(path)
        try:
            front, body = split_frontmatter(files[path].decode("utf-8"))
        except UnicodeError:
            raise VaultError("markdown_must_be_utf8") from None
        if front.get("item_id") != row["id"] or front.get("version") != row["user_edit_version"]:
            raise VaultError("frontmatter_identity_mismatch")
        originals = row.get("portable_links", {})
        if not isinstance(originals, dict):
            raise VaultError("invalid_link_mapping")
        row["note"] = rewrite_links(body, lambda destination: originals.get(destination))
        if digest(row["note"]) != row.get("note_sha256"):
            raise VaultError("raw_note_hash_mismatch")
    if set(files) != declared:
        raise VaultError("unexpected_archive_file")
    validate_payload(payload)
    return payload, digest(content)


def parse_plain_markdown(files, owner):
    """Proven subset: UTF8 MD and JSON-valued frontmatter, no plugins/media."""
    if any(not name.lower().endswith((".md", ".markdown")) for name in files):
        raise VaultError("plain_vault_only_markdown_supported")
    payload = {name: [] for name in (*GROUPS, *RELATIONS, *ROW_MODELS, "items")}
    aliases = {}
    for path, content in sorted(files.items()):
        try:
            front, body = split_frontmatter(content.decode("utf-8"))
        except UnicodeError:
            raise VaultError("markdown_must_be_utf8") from None
        item_id = str(UUID(front["item_id"])) if "item_id" in front else str(uuid5(NAMESPACE_URL, f"kt-vault:{owner.pk}:{path}"))
        row = {"id": item_id, "kind": "text", "title": posixpath.basename(path).rsplit(".", 1)[0], "description": "", "note": body, "user_edit_version": front.get("version", 0), "saved_at": front.get("saved_at") or datetime.now().astimezone().isoformat(), "published_at": front.get("published_at"), "updated_at": front.get("saved_at") or datetime.now().astimezone().isoformat(), "deleted_at": None, "favorite": False, "classification_status": "unclassified", "source_fetch": "not_applicable", "asset_storage": "not_applicable", "content_extract": "not_available", "home_topic_id": None, "parent_item_id": None, "outline_order": 0, "structure_version": 0, "structure_origin": "user"}
        payload["items"].append(row)
        aliases[path] = item_id
    stems = {}
    for path, key in aliases.items():
        stems.setdefault(posixpath.basename(path).rsplit(".", 1)[0], []).append(key)
    for path, row in zip(sorted(files), payload["items"], strict=True):
        def standard(destination):
            if "://" in destination or destination.startswith("#"):
                return None
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), unquote(destination)))
            return "#/muc/" + aliases[resolved] if resolved in aliases else None
        row["note"] = rewrite_links(row["note"], standard)
        # Only unique simple prose wiki links are supported, never guessed by title.
        lines, fence = [], False
        for line in row["note"].splitlines(keepends=True):
            if re.match(r"^ {0,3}(`{3,}|~{3,})", line):
                fence = not fence
                lines.append(line)
                continue
            if not fence and "`" not in line:
                def wiki(match):
                    target, _, label = match[1].partition("|")
                    keys = stems.get(target, [])
                    if len(keys) != 1:
                        raise VaultError("unresolved_or_ambiguous_wiki_link")
                    return "[" + (label or target).replace("[", "").replace("]", "") + "](#/muc/" + keys[0] + ")"
                line = re.sub(r"(?<!\\)\[\[([^\]\n]+)\]\]", wiki, line)
            lines.append(line)
        row["note"] = "".join(lines)
    validate_payload(payload)
    return payload


def validate_payload(data):
    required = {*GROUPS, *RELATIONS, *ROW_MODELS, "items"}
    if set(data) != required or any(not isinstance(data[key], list) for key in required) or len(data["items"]) > MAX_ITEMS:
        raise VaultError("invalid_vault_collections")
    items = {row["id"]: row for row in data["items"]}
    if len(items) != len(data["items"]):
        raise VaultError("duplicate_identity")
    for row in data["items"]:
        UUID(row["id"])
        if len(row.get("note", "")) > 100_000 or "\0" in row.get("note", "") or type(row["user_edit_version"]) is not int or row["user_edit_version"] < 0:
            raise VaultError("invalid_note")
        for key in ("saved_at", "updated_at", "published_at", "deleted_at"):
            if row.get(key) and datetime.fromisoformat(row[key]).tzinfo is None:
                raise VaultError("timezone_required")
    tree_check(data["items"], "parent_item_id")
    tree_check(data["topics"], "parent_id")
    for name, model in GROUPS.items():
        seen = set()
        for row in data[name]:
            if type(row["id"]) is not int or row["id"] < 1:
                raise VaultError("invalid_group_identity")
            normalized = (row.get("parent_id") if name == "topics" else None, unicodedata.normalize("NFC", row["name"]).casefold())
            if normalized in seen:
                raise VaultError("duplicate_group_name")
            seen.add(normalized)
    group_ids = {name: {row["id"] for row in data[name]} for name in GROUPS}
    for row in data["items"]:
        if row["home_topic_id"] is not None and row["home_topic_id"] not in group_ids["topics"]:
            raise VaultError("missing_home_folder")
    for name, (_, field) in RELATIONS.items():
        if any(row["item_id"] not in items or row[field + "_id"] not in group_ids[field + "s"] for row in data[name]):
            raise VaultError("invalid_membership")
    for name in ("sources", "assets", "parts", "events", "clips"):
        if any(row["item_id"] not in items for row in data[name]):
            raise VaultError("unresolved_item")
        if len({str(row["id"]) for row in data[name]}) != len(data[name]):
            raise VaultError("duplicate_identity")
    for row in data["sources"]:
        check_url(row["original_url"])
        check_url(row["canonical_url"])
    assets = {row["id"]: row for row in data["assets"]}
    parts = {row["id"]: row for row in data["parts"]}
    sources = {row["id"]: row for row in data["sources"]}
    events = {row["id"]: row for row in data["events"]}
    for row in data["parts"]:
        if row["asset_id"] and (row["asset_id"] not in assets or assets[row["asset_id"]]["item_id"] != row["item_id"]):
            raise VaultError("cross_item_asset")
        source_id = row.get("source_locator", {}).get("source_id")
        if source_id is not None and (source_id not in sources or sources[source_id]["item_id"] != row["item_id"]):
            raise VaultError("cross_item_source")
    if any(row["asset_id"] not in assets for row in data["locations"]):
        raise VaultError("unresolved_asset")
    for row in data["clips"]:
        if row["capture_id"] not in events or events[row["capture_id"]]["item_id"] != row["item_id"] or (row["quote_hash"] and digest(row["quote"]) != row["quote_hash"]):
            raise VaultError("invalid_clip")
        for field, mapping in (("source_id", sources), ("part_id", parts), ("asset_id", assets)):
            if row[field] is not None and (row[field] not in mapping or mapping[row[field]]["item_id"] != row["item_id"]):
                raise VaultError("invalid_clip_reference")
    for row in data["collections"]:
        CollectionQuery.model_validate(row["query"])
    if SECRET.search(json_bytes(data).decode()):
        raise VaultError("sensitive_input_blocked")


def baseline(owner, ids):
    rows = list(Item.objects.filter(owner=owner, pk__in=ids).order_by("id").values("id", "note", "title", "description", "user_edit_version", "structure_version"))
    return digest(json_bytes(rows))


def statuses(owner, data):
    existing = {str(item.pk): item for item in Item.objects.filter(pk__in=[row["id"] for row in data["items"]])}
    rows = []
    for row in data["items"]:
        local = existing.get(row["id"])
        status = "new" if local is None else "conflict"
        if local and local.owner_id == owner.pk and not local.deleted_at:
            if local.user_edit_version == row["user_edit_version"] and local.note == row["note"] and local.title == row["title"] and local.description == row["description"] and local.structure_version == row["structure_version"]:
                status = "unchanged"
            elif local.user_edit_version < row["user_edit_version"] and local.structure_version <= row["structure_version"]:
                status = "update"
        rows.append({"item_id": row["id"], "title": row["title"], "status": status, "before": local.note if local and local.owner_id == owner.pk else None, "after": row["note"], "version": row["user_edit_version"]})
    return rows


def preview(owner, content):
    data, archive_hash = parse_vault(content, owner)
    rows = statuses(owner, data)
    counts = {state: sum(row["status"] == state for row in rows) for state in ("new", "update", "unchanged", "conflict")}
    receipt = signing.dumps({"owner": owner.pk, "archive": archive_hash, "baseline": baseline(owner, [row["id"] for row in data["items"]])}, salt=SALT, compress=True)
    return {"rows": rows[:100], "counts": counts, "more_count": max(0, len(rows) - 100), "receipt": receipt, "media_not_included": len(data["assets"]), "metadata": {key: len(data[key]) for key in ("topics", "events", "sources", "assets", "parts", "clips", "collections")}, "format": "portable_markdown", "warnings": ["Original media are not included or verified. Imported mappings stay pending.", "Existing folder names and pinned memberships are retained on update."]}


def make(model, row, **extra):
    value = model.objects.create(**row, **extra)
    timestamps = {key: row[key] for key in ("created_at", "updated_at") if key in row}
    if timestamps:
        model.objects.filter(pk=value.pk).update(**timestamps)
    return value


def reusable(model, owner, row, *, item_id=None):
    existing = model.objects.filter(pk=row["id"]).first()
    if existing is None:
        return None
    if hasattr(existing, "owner_id"):
        same_owner = existing.owner_id == owner.pk
    else:
        same_owner = existing.item.owner_id == owner.pk
    return existing if same_owner and (item_id is None or str(existing.item_id) == item_id) else False


@transaction.atomic
def apply_import(owner, content, receipt, selected):
    data, archive_hash = parse_vault(content, owner)
    try:
        token = signing.loads(receipt, salt=SALT, max_age=900)
    except signing.BadSignature:
        raise VaultError("invalid_or_expired_preview") from None
    if token.get("owner") != owner.pk or token.get("archive") != archive_hash:
        raise VaultError("preview_scope_mismatch")
    get_user_model().objects.select_for_update().get(pk=owner.pk)
    rows = statuses(owner, data)
    if not isinstance(selected, list) or len(selected) > MAX_ITEMS or any(not isinstance(key, str) for key in selected):
        raise VaultError("invalid_selection")
    selected = set(selected)
    by_id = {row["item_id"]: row for row in rows}
    if not selected <= by_id.keys() or any(by_id[key]["status"] == "conflict" for key in selected):
        raise VaultError("import_conflict")
    if all(by_id[key]["status"] == "unchanged" for key in selected):
        return {"state": "unchanged", "created": 0, "updated": 0, "events_created": 0}
    if baseline(owner, by_id) != token["baseline"]:
        raise VaultError("preview_database_changed")
    available = selected | {str(key) for key in Item.objects.filter(owner=owner, pk__in=by_id).values_list("pk", flat=True)}
    if any(row["parent_item_id"] and row["parent_item_id"] not in available for row in data["items"] if row["id"] in selected):
        raise VaultError("selection_missing_parent")
    maps = {name: {} for name in (*GROUPS, "sources", "parts")}
    for name, model in GROUPS.items():
        pending = list(data[name])
        while pending:
            next_round = []
            for original in pending:
                if name == "topics" and original["parent_id"] is not None and original["parent_id"] not in maps[name]:
                    next_round.append(original)
                    continue
                row = {key: original[key] for key in GROUP_FIELDS[name]}
                if name == "topics":
                    row["parent_id"] = maps[name].get(row["parent_id"])
                existing = reusable(model, owner, row)
                if existing is False:
                    row.pop("id")
                    existing = model.objects.filter(owner=owner, name=row["name"], **({"parent_id": row["parent_id"]} if name == "topics" else {})).first()
                value = existing or make(model, row, owner=owner)
                maps[name][original["id"]] = value.pk
            if len(next_round) == len(pending):
                raise VaultError("invalid_hierarchy")
            pending = next_round
    created, updated = 0, 0
    for source in data["items"]:
        key = source["id"]
        if key not in selected or by_id[key]["status"] == "unchanged":
            continue
        fields = {name: source[name] for name in ITEM_FIELDS if name not in {"id", "home_topic_id", "parent_item_id"}}
        fields["note"] = source["note"]
        if by_id[key]["status"] == "new":
            make(Item, fields, id=key, owner=owner)
            created += 1
        else:
            # saved_at is immutable even if the package contains another timestamp.
            fields.pop("saved_at")
            Item.objects.filter(pk=key, owner=owner).update(**fields)
            updated += 1
    for source in data["items"]:
        if source["id"] in selected:
            Item.objects.filter(pk=source["id"], owner=owner).update(home_topic_id=maps["topics"].get(source["home_topic_id"]), parent_item_id=source["parent_item_id"])
    for name, (model, field) in RELATIONS.items():
        for source in data[name]:
            if source["item_id"] not in selected:
                continue
            defaults = {key: source[key] for key in RELATION_FIELDS if key not in {"id", "item_id"}}
            model.objects.get_or_create(item_id=source["item_id"], **{field + "_id": maps[field + "s"][source[field + "_id"]]}, defaults=defaults)
    for source in data["sources"]:
        if source["item_id"] not in selected:
            continue
        row = dict(source)
        existing = reusable(Source, owner, row, item_id=row["item_id"])
        if existing is False:
            row.pop("id")
            existing = Source.objects.filter(item_id=row["item_id"], identity_hash=row["identity_hash"], original_url=row["original_url"]).first()
        value = existing or make(Source, row)
        maps["sources"][source["id"]] = value.pk
    for source in data["assets"]:
        if source["item_id"] not in selected:
            continue
        current = Asset.objects.filter(pk=source["id"]).first()
        if current and (str(current.item_id) != source["item_id"] or current.item.owner_id != owner.pk or current.sha256 != source["sha256"]):
            raise VaultError("asset_identity_conflict")
        if current is None:
            make(Asset, dict(source))
    for source in data["locations"]:
        asset = next(row for row in data["assets"] if row["id"] == source["asset_id"])
        if asset["item_id"] not in selected:
            continue
        existing = StorageLocation.objects.filter(provider=source["provider"], provider_file_id=source["provider_file_id"]).first() if source["provider_file_id"] else None
        if existing and str(existing.asset_id) != source["asset_id"]:
            raise VaultError("asset_mapping_conflict")
        if not StorageLocation.objects.filter(asset_id=source["asset_id"], provider=source["provider"]).exists():
            row = {key: value for key, value in source.items() if key != "id"}
            row.update(status="pending", verified_at=None)
            make(StorageLocation, row)
    for source in data["parts"]:
        if source["item_id"] not in selected:
            continue
        row = dict(source)
        row["source_locator"] = dict(row["source_locator"])
        if "source_id" in row["source_locator"]:
            row["source_locator"]["source_id"] = maps["sources"][row["source_locator"]["source_id"]]
        existing = reusable(DerivedContent, owner, row, item_id=row["item_id"])
        if existing is False:
            row.pop("id")
            existing = DerivedContent.objects.filter(item_id=row["item_id"], kind=row["kind"], input_hash=row["input_hash"], processor=row["processor"], processor_version=row["processor_version"], text=row["text"]).first()
        value = existing or make(DerivedContent, row)
        maps["parts"][source["id"]] = value.pk
    events_created = 0
    for source in data["events"]:
        if source["item_id"] not in selected:
            continue
        existing = CaptureEvent.objects.filter(pk=source["id"]).first()
        if existing:
            if existing.owner_id != owner.pk or str(existing.item_id) != source["item_id"] or existing.raw_text != source["raw_text"] or existing.server_received_at.isoformat() != source["server_received_at"]:
                raise VaultError("capture_identity_conflict")
        else:
            make(CaptureEvent, dict(source), owner=owner)
            events_created += 1
    for row in data["items"]:
        if row["id"] in selected and not any(event["item_id"] == row["id"] for event in data["events"]):
            # Plain Markdown has no historical Event. This explicit import is
            # one new submission, deterministic per owner/item for retries.
            _, fresh = CaptureEvent.objects.get_or_create(owner=owner, item_id=row["id"], source_channel="vault_import", idempotency_key="vault:" + row["id"], defaults={"raw_kind": "text", "raw_text": row["note"] or row["title"] or "Imported note"})
            events_created += int(fresh)
    for source in data["clips"]:
        if source["item_id"] not in selected:
            continue
        row = dict(source)
        row["source_id"] = maps["sources"].get(row["source_id"])
        row["part_id"] = maps["parts"].get(row["part_id"])
        existing = ClipAnnotation.objects.filter(pk=row["id"]).first()
        if existing and (existing.item.owner_id != owner.pk or str(existing.item_id) != row["item_id"]):
            raise VaultError("clip_identity_conflict")
        if not existing:
            make(ClipAnnotation, row)
    for source in data["collections"]:
        row = dict(source)
        query = row["query"]
        for field in ("topics", "projects", "tags"):
            for mode in ("any", "all", "exclude"):
                if field in query:
                    query[field][mode] = [maps[field][key] for key in query[field].get(mode, [])]
        CollectionQuery.model_validate(query)
        existing = SavedCollection.objects.filter(pk=row["id"]).first()
        if existing and existing.owner_id != owner.pk:
            raise VaultError("collection_identity_conflict")
        if not existing:
            make(SavedCollection, row, owner=owner)
    for row in data["items"]:
        if row["id"] in selected and by_id[row["id"]]["status"] != "unchanged":
            JobRepository.enqueue(kind="organize", item=Item.objects.get(pk=row["id"]), idempotency_key="vault:" + archive_hash + ":" + row["id"], input_ref={"item_id": row["id"]})
    return {"state": "imported", "created": created, "updated": updated, "events_created": events_created, "media_verified": 0}
