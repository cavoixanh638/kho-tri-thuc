"""P08/J8: real two-database portable Vault roundtrip, synthetic QA only.

Called through Django manage.py shell inside the isolated kt-p08-ci Compose job.
Source is the already exercised browser QA PostgreSQL, target is a separately
created/migrated *empty* PostgreSQL database. Never touches external providers.
"""
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

from django.contrib.auth import get_user_model
from django.db import connection
from catalog.models import Item, ItemTopic, Source, Topic
from catalog.vault import apply_import, export_vault, parse_vault, preview_import
from ingestion.models import CaptureEvent
from storage.models import Asset

ROOT = Path("/tmp/p08-vault-clean")
SOURCE_DB = "kt_p08_journeys"
TARGET_DB = "kt_p08_vault_clean"
USER = "p08-fixture"


def require(condition, code):
    if not condition:
        raise AssertionError("P08_J8_" + code)


def guard(mode):
    require(os.environ.get("P08_VAULT_ISOLATED") == "YES", "ISOLATION_FLAG_REQUIRED")
    db_name = connection.settings_dict["NAME"]
    require(db_name == (SOURCE_DB if mode == "source" else TARGET_DB),
            "UNEXPECTED_DATABASE")
    require(os.environ.get("P08_VAULT_MODE") == mode, "MODE_MISMATCH")
    ROOT.mkdir(mode=0o700, exist_ok=True)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def counts(data):
    return {name: len(data[name])
            for name in ("items", "topics", "item_topics", "events", "assets", "sources")}


def source():
    guard("source")
    owner = get_user_model().objects.get(username=USER)
    items = list(Item.objects.filter(owner=owner).order_by("id"))
    topics = list(Topic.objects.filter(owner=owner))
    require(len(items) == 2, "EXPECTED_TWO_BROWSER_ITEMS")
    require(len(topics) == 2, "EXPECTED_TWO_BROWSER_TOPICS")
    require(all(row.title.startswith("P08 ") for row in items), "NON_FIXTURE_ITEM")
    require(all(row.name.startswith("P08 ") for row in topics), "NON_FIXTURE_TOPIC")
    require(len([row for row in items if row.parent_item_id]) == 1,
            "BROWSER_PARENT_CHILD_NOT_PRESENT")
    require(ItemTopic.objects.filter(item__owner=owner).count() >= 3,
            "BROWSER_SHORTCUT_NOT_PRESENT")

    # Explicit synthetic source/asset/event *metadata*, with no bytes on Drive.
    # The browser journey already checked human-authored notes before this step.
    child = next(row for row in items if row.parent_item_id)
    Source.objects.get_or_create(
        item=child, identity_hash=sha(b"p08-j8-source-only"),
        original_url="https://example.org/p08-j8-fixture",
        canonical_url="https://example.org/p08-j8-fixture",
        defaults={"platform": "web"},
    )
    Asset.objects.get_or_create(
        item=child, original_filename="p08-j8-metadata-only.pdf",
        defaults={"role": "original", "mime": "application/pdf", "size": 29,
                  "sha256": sha(b"p08-j8-synthetic-no-media-upload"),
                  "content_version": 1},
    )
    CaptureEvent.objects.get_or_create(
        owner=owner, source_channel="p08-j8-synthetic",
        idempotency_key="p08-j8-vault-source-fixture-v1",
        defaults={"item": child, "raw_kind": "text",
                  "raw_text": "P08 synthetic archive event (no user data)"},
    )

    archive = export_vault(owner)
    data, archive_hash = parse_vault(archive)
    stats = counts(data)
    require(stats["items"] == 2 and stats["topics"] == 2, "EXPORT_COUNT")
    require(stats["item_topics"] >= 3, "EXPORT_SHORTCUT")
    require(stats["assets"] >= 1 and stats["events"] >= 1
            and stats["sources"] >= 1, "EXPORT_PROVENANCE")
    require(any(row["parent_item_id"] for row in data["items"]), "EXPORT_PARENT")
    ROOT.joinpath("archive.zip").write_bytes(archive)
    report = {
        "schema": 1, "mode": "source", "status": "PASS",
        "source_database": SOURCE_DB, "archive_sha256": archive_hash,
        "archive_bytes": len(archive), "counts": stats,
        "browser_seeded_items": 2, "synthetic_metadata_only": True,
        "external_drive_calls": 0, "external_ai_calls": 0,
        "media_verified": 0,
    }
    ROOT.joinpath("source.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"mode": "source", "status": report["status"],
                      "archive_sha256": archive_hash, "counts": stats}))


def target():
    guard("target")
    require(not Item.objects.exists() and not Topic.objects.exists()
            and not CaptureEvent.objects.exists() and not Asset.objects.exists(),
            "TARGET_NOT_EMPTY")
    owner = get_user_model().objects.create_user(
        username=USER, password=None)
    archive = ROOT.joinpath("archive.zip").read_bytes()
    manifest, archive_hash = parse_vault(archive)
    expected = counts(manifest)
    preview = preview_import(owner, archive)
    require(preview["counts"]["new"] == expected["items"], "PREVIEW_NOT_ALL_NEW")
    require(preview["counts"]["conflict"] == 0, "PREVIEW_CONFLICT")
    applied = apply_import(owner, archive, preview["receipt"], ["*"])
    require(applied["state"] == "imported"
            and applied["created"] == expected["items"], "IMPORT_FAILED")
    require(applied["events_created"] == expected["events"]
            and applied["assets_created"] == expected["assets"], "PROVENANCE_IMPORT")
    require(applied["media_verified"] == 0, "FALSE_MEDIA_VERIFICATION")

    original_items = {row["id"]: row for row in manifest["items"]}
    require(Item.objects.filter(owner=owner).count() == len(original_items),
            "ITEM_COUNT_CHANGED")
    topic_by_old_id = {row["id"]: row for row in manifest["topics"]}
    imported_topics = {row.name: row for row in Topic.objects.filter(owner=owner)}
    require(len(imported_topics) == expected["topics"], "TOPIC_COUNT_CHANGED")
    require(len(topic_by_old_id) == len(imported_topics), "TOPIC_COLLISION")
    for row in manifest["topics"]:
        restored = imported_topics[row["name"]]
        parent = topic_by_old_id.get(row["parent_id"])
        require((restored.parent.name if restored.parent_id else None)
                == (parent["name"] if parent else None), "TOPIC_PARENT_CHANGED")

    for ident, old in original_items.items():
        restored = Item.objects.get(pk=ident, owner=owner)
        require(restored.note == old["_note"]
                and sha(restored.note.encode("utf-8")) == old["note_sha256"],
                "MARKDOWN_BYTES_CHANGED")
        require(restored.title == old["title"], "TITLE_CHANGED")
        require((str(restored.parent_item_id) if restored.parent_item_id else None)
                == old["parent_item_id"], "PARENT_UUID_CHANGED")
        require((restored.home_topic.name if restored.home_topic_id else None)
                == (topic_by_old_id[old["home_topic_id"]]["name"]
                    if old["home_topic_id"] is not None else None),
                "HOME_FOLDER_CHANGED")
        require(restored.saved_at == datetime.fromisoformat(old["saved_at"]),
                "RECEIPT_TIME_CHANGED")

    expected_memberships = {
        (row["item_id"], topic_by_old_id[row["topic_id"]]["name"],
         row["origin"], row["user_pinned"]) for row in manifest["item_topics"]
    }
    actual_memberships = {
        (str(row.item_id), row.topic.name, row.origin, row.user_pinned)
        for row in ItemTopic.objects.filter(item__owner=owner).select_related("topic")
    }
    require(actual_memberships == expected_memberships, "SHORTCUT_OR_MEMBERSHIP_CHANGED")

    for old in manifest["events"]:
        restored = CaptureEvent.objects.get(pk=old["id"], owner=owner)
        require(str(restored.item_id) == old["item_id"]
                and restored.raw_text == old["raw_text"]
                and restored.server_received_at == datetime.fromisoformat(
                    old["server_received_at"]), "EVENT_HISTORY_CHANGED")
    for old in manifest["assets"]:
        restored = Asset.objects.get(pk=old["id"], item__owner=owner)
        require(str(restored.item_id) == old["item_id"]
                and restored.sha256 == old["sha256"]
                and restored.size == old["size"], "ASSET_METADATA_CHANGED")
        require(not restored.locations.exists(), "FAKE_DRIVE_VERIFICATION")
    for old in manifest["sources"]:
        require(Source.objects.filter(
            item_id=old["item_id"], identity_hash=old["identity_hash"],
            original_url=old["original_url"]).exists(), "SOURCE_IDENTITY_CHANGED")

    replay = apply_import(owner, archive, preview["receipt"], ["*"])
    require(replay["state"] == "unchanged" and replay["events_created"] == 0
            and replay["assets_created"] == 0, "REPLAY_NOT_IDEMPOTENT")
    require(CaptureEvent.objects.filter(owner=owner).count() == expected["events"],
            "EVENT_DUPLICATED")
    require(Asset.objects.filter(item__owner=owner).count() == expected["assets"],
            "ASSET_DUPLICATED")

    result = {
        "schema": 1, "task": "P08/J8", "status": "PASS",
        "source_database": SOURCE_DB, "target_database": TARGET_DB,
        "archive_sha256": archive_hash, "counts": expected,
        "created": applied["created"], "events_created": applied["events_created"],
        "assets_created": applied["assets_created"], "replay_unchanged": True,
        "note_sha256_verified": True, "uuid_parent_verified": True,
        "folder_hierarchy_verified": True, "home_shortcut_verified": True,
        "source_identity_verified": True, "capture_time_verified": True,
        "asset_metadata_sha256_verified": True,
        "media_verified": 0, "metadata_only": True,
        "external_drive_calls": 0, "external_ai_calls": 0,
    }
    ROOT.joinpath("result.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"task": "P08/J8", "status": "PASS",
                      "archive_sha256": archive_hash, "counts": expected}))


def main():
    mode = os.environ.get("P08_VAULT_MODE")
    require(mode in ("source", "target"), "INVALID_MODE")
    (source if mode == "source" else target)()


main()
