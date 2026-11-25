"""Create, verify, and restore Kho Tri Thuc PostgreSQL 18 backup bundles."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DUMP = "database.dump"
MANIFEST = "manifest.json"
CHECKSUMS = "SHA256SUMS"
SCHEMA_VERSION = 5
SUPPORTED_SCHEMA_VERSIONS = (1, 2, 3, 4, 5)
PG_MAJOR = 18

# The projection is part of the versioned format. Keep credential tables and
# opaque payloads (Source.metadata, DerivedContent.source_locator, Job.input_ref)
# out of the export. The dump keeps the opaque application payloads.
COLLECTIONS = {
    "items": (
        "catalog_item",
        "id, owner_id, kind, title, description, note, saved_at, published_at, "
        "updated_at, favorite, deleted_at, user_edit_version, classification_status",
    ),
    "capture_events": (
        "ingestion_captureevent",
        "id, owner_id, item_id, source_channel, raw_kind, raw_text, original_url, "
        "server_received_at, client_sent_at, idempotency_key, status",
    ),
    "sources": (
        "catalog_source",
        "id, item_id, original_url, canonical_url, identity_hash, platform, "
        "platform_id, captured_at, published_at",
    ),
    "topics": (
        "catalog_topic",
        "id, owner_id, name, parent_id, archived, node_kind, sort_order",
    ),
    "projects": ("catalog_project", "id, owner_id, name, description, archived"),
    "tags": ("catalog_tag", "id, owner_id, name"),
    "item_topics": (
        "catalog_itemtopic",
        "id, item_id, topic_id, origin, user_pinned, confidence, method_version, source_version",
    ),
    "item_projects": (
        "catalog_itemproject",
        "id, item_id, project_id, origin, user_pinned, confidence, method_version, source_version",
    ),
    "item_tags": (
        "catalog_itemtag",
        "id, item_id, tag_id, origin, user_pinned, confidence, method_version, source_version",
    ),
    "assets": (
        "storage_asset",
        "id, item_id, role, mime, size, sha256, original_filename, content_version",
    ),
    "storage_locations": (
        "storage_storagelocation",
        "id, asset_id, provider, provider_file_id, status, verified_at, "
        "provider_modified_at, provider_revision",
    ),
    "derived_contents": (
        "processing_derivedcontent",
        "id, item_id, asset_id, kind, text, processor, processor_version, "
        "input_hash, status, created_at",
    ),
    "related_items": (
        "catalog_relateditem",
        "id, item_a_id, item_b_id, relation_type, reason, confidence, "
        "method_version, source_version, status",
    ),
    "jobs": (
        "jobs_job",
        "id, item_id, kind, idempotency_key, state, attempt, retry_at, "
        "lease_until, error_code, created_at, completed_at",
    ),
    "knowledge_exports": (
        "storage_knowledgeexport",
        "id, item_id, enabled, format, provider, provider_file_id, source_version, "
        "exported_version, content_sha256, status, truncated, last_error, last_synced_at",
    ),
}

# v1–v3 are immutable wire formats. v4 adds Item's structural fields and two
# separate tables; it does not change Asset, Source or CaptureEvent projections.
V4_ITEM_FIELDS = (
    COLLECTIONS["items"][0],
    COLLECTIONS["items"][1]
    + ", home_topic_id, parent_item_id, outline_order, structure_version, structure_origin",
)
V4_COLLECTIONS = {
    "saved_collections": (
        "catalog_savedcollection",
        "id, owner_id, name, normalized_name, query, view, version, created_at, updated_at",
    ),
    "clip_annotations": (
        "processing_clipannotation",
        "id, item_id, capture_id, source_id, part_id, asset_id, mode, quote, "
        "quote_hash, source_version, processor_version, locator, source_url, "
        "page_title, verification, inserted_edit_version, created_at",
    ),
}


def collections_for_version(schema_version):
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise BackupError("Unsupported backup manifest format.")
    projection = dict(COLLECTIONS)
    if schema_version == 1:
        projection.pop("knowledge_exports")
    if schema_version < 3:
        projection["topics"] = (
            "catalog_topic", "id, owner_id, name, parent_id, archived",
        )
    if schema_version >= 4:
        projection["items"] = V4_ITEM_FIELDS
        projection.update(V4_COLLECTIONS)
    if schema_version >= 5:
        projection["excluded_topics"] = ("catalog_itemtopicexclusion", "id, item_id, topic_id")
    return projection


TRANSACTION = (
    b"BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;\n"
    b"SET LOCAL TIME ZONE 'UTC';\n"
    b"SET LOCAL DateStyle TO 'ISO, YMD';\n"
    b"SET LOCAL lock_timeout TO '10s';\n"
)
EMPTY_DATABASE = b"""
SELECT NOT EXISTS (
    SELECT FROM pg_catalog.pg_namespace
    WHERE nspname NOT IN ('pg_catalog', 'pg_toast', 'information_schema', 'public')
      AND nspname !~ '^pg_(toast_)?temp_[0-9]+$'
    UNION ALL SELECT FROM pg_catalog.pg_class
    WHERE relnamespace = 'public'::regnamespace
    UNION ALL SELECT FROM pg_catalog.pg_proc
    WHERE pronamespace = 'public'::regnamespace
    UNION ALL SELECT FROM pg_catalog.pg_type
    WHERE typnamespace = 'public'::regnamespace
    UNION ALL SELECT FROM pg_catalog.pg_extension WHERE extname <> 'plpgsql'
);
"""
PSQL_ARGS = ("-X", "-qAt", "--no-password", "--set=ON_ERROR_STOP=1", "--file=-")


class BackupError(Exception):
    pass


class Postgres:
    def __init__(self, compose):
        self.compose = compose

    def command(self, tool, args):
        if not self.compose:
            return [tool, *args]
        return [
            "docker",
            "compose",
            "exec",
            "-T",
            "db",
            "sh",
            "-ec",
            'export PGUSER="$POSTGRES_USER" PGDATABASE="$POSTGRES_DB" '
            'PGPASSWORD="$POSTGRES_PASSWORD" PGHOST=127.0.0.1 '
            'PGCLIENTENCODING=UTF8 PGCONNECT_TIMEOUT=10; exec "$@"',
            "kt-backup",
            tool,
            *args,
        ]

    def options(self):
        env = {**os.environ, "PGCLIENTENCODING": "UTF8"}
        env.setdefault("PGCONNECT_TIMEOUT", "10")
        return {
            "cwd": ROOT if self.compose else None,
            "env": env,
            "stderr": subprocess.DEVNULL,
        }

    def run(self, tool, *args, input=None, stdin=None, output=subprocess.PIPE):
        if input is None and stdin is None:
            stdin = subprocess.DEVNULL
        result = subprocess.run(
            self.command(tool, args),
            input=input,
            stdin=stdin,
            stdout=output,
            **self.options(),
        )
        self.check(result.returncode, tool)
        return result.stdout

    def psql(self, sql, target=None):
        args = (*PSQL_ARGS, f"--dbname={target}") if target else PSQL_ARGS
        return self.run("psql", *args, input=sql).strip()

    def snapshot(self):
        return subprocess.Popen(
            self.command("psql", PSQL_ARGS),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            **self.options(),
        )

    def require_version(self, tool):
        version = self.run(tool, "--version")
        if not re.search(
            rb"\(PostgreSQL\) " + str(PG_MAJOR).encode() + rb"(?:\.|\s)", version
        ):
            raise BackupError(f"{tool} must be from PostgreSQL {PG_MAJOR}.")

    def require_server(self, target=None):
        version = self.psql(
            b"SELECT current_setting('server_version_num')::int / 10000;", target
        )
        if version != str(PG_MAJOR).encode():
            raise BackupError(f"The database must use PostgreSQL {PG_MAJOR}.")

    @staticmethod
    def check(returncode, tool):
        if returncode:
            # PostgreSQL error detail can include connection secrets or row contents.
            raise BackupError(
                f"{tool} failed (exit {returncode}). Check the local database logs."
            )


def manifest_select(names=None, schema_version=SCHEMA_VERSION):
    projection = collections_for_version(schema_version)
    if names is not None and set(names) != set(projection):
        raise BackupError("Missing or invalid manifest collections.")
    parts = [
        f"'{name}', (SELECT COALESCE(json_agg(r ORDER BY r.id), '[]'::json) "
        f"FROM (SELECT {columns} FROM public.{table}) r)"
        for name, (table, columns) in projection.items()
    ]
    return "SELECT json_build_object(\n" + ",\n".join(parts) + "\n)"


def manifest_query(names=None, schema_version=SCHEMA_VERSION):
    # The COMMIT closes the read-only pg_export_snapshot transaction.
    return (manifest_select(names, schema_version) + ";\nCOMMIT;\n").encode()


def record_backup(pg, directory):
    with pg.snapshot() as session:
        try:
            session.stdin.write(TRANSACTION + b"SELECT pg_export_snapshot();\n")
            session.stdin.flush()
            snapshot = session.stdout.readline().strip()
            if not re.fullmatch(rb"[0-9A-Fa-f-]+", snapshot):
                raise BackupError("psql could not export the backup snapshot.")

            with (directory / DUMP).open("wb") as archive:
                pg.run(
                    "pg_dump",
                    "--format=custom",
                    "--no-password",
                    "--lock-wait-timeout=10s",
                    f"--snapshot={snapshot.decode('ascii')}",
                    "--exclude-table-data=public.storage_driveaccount",
                    "--exclude-table-data=public.django_session",
                    output=archive,
                )
            rows, _ = session.communicate(manifest_query())
            pg.check(session.returncode, "psql")
        finally:
            if session.poll() is None:
                session.kill()

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "postgres_major": PG_MAJOR,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "collections": json.loads(rows),
    }
    (directory / MANIFEST).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (directory / CHECKSUMS).write_text(
        checksum_lines(directory), encoding="ascii", newline="\n"
    )


def checksum_lines(directory):
    records = []
    for filename in (DUMP, MANIFEST):
        with (directory / filename).open("rb") as stream:
            sha = hashlib.file_digest(stream, "sha256").hexdigest()
        records.append(f"{sha}  {filename}\n")
    return "".join(records)


def verify_bundle(directory):
    if (directory / CHECKSUMS).read_text(encoding="ascii") != checksum_lines(directory):
        raise BackupError("Backup checksum mismatch.")
    manifest = json.loads((directory / MANIFEST).read_text(encoding="utf-8"))
    if (
        not isinstance(manifest, dict)
        or type(manifest.get("schema_version")) is not int
        or manifest["schema_version"] not in SUPPORTED_SCHEMA_VERSIONS
        or manifest.get("postgres_major") != PG_MAJOR
    ):
        raise BackupError("Unsupported backup manifest format.")
    collections = manifest.get("collections")
    if (
        not isinstance(collections, dict)
        or set(collections) != set(collections_for_version(manifest["schema_version"]))
        or any(not isinstance(rows, list) for rows in collections.values())
    ):
        raise BackupError("Missing or invalid manifest collections.")
    return collections


def create(pg, destination):
    if not pg.compose and not os.getenv("PGDATABASE"):
        raise BackupError("Set PGDATABASE to the source database for native backup.")
    if destination.exists():
        raise BackupError("Choose a new output directory.")
    pg.require_version("psql")
    pg.require_version("pg_dump")
    pg.require_server()

    with tempfile.TemporaryDirectory(
        prefix=".kt-backup-", dir=destination.parent
    ) as path:
        staging = Path(path) / "bundle"
        staging.mkdir()
        record_backup(pg, staging)
        verify_bundle(staging)
        staging.rename(destination)


def restore_assertion_sql(expected, schema_version):
    """Verify the full versioned projection BEFORE commit, never post-commit.

    Hex-encode the expected JSON: note/URL/quote contents cannot break SQL
    quoting, PL/pgSQL dollar delimiters, or trigger psql metacommands.
    """
    expected_json = json.dumps(
        expected, sort_keys=True, ensure_ascii=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8").hex()
    select = manifest_select(expected, schema_version)
    return (
        # Compare timestamp strings in the same representation used at capture.
        # The target database can have a different time zone or date style.
        "\nSET LOCAL TIME ZONE 'UTC';\nSET LOCAL DateStyle TO 'ISO, YMD';\n"
        "DO $kt_backup_assert$\nBEGIN\n"
        "    IF (" + select + ")::jsonb IS DISTINCT FROM "
        "convert_from(decode('" + expected_json + "', 'hex'), 'UTF8')::jsonb THEN\n"
        "        RAISE EXCEPTION 'Restore manifest projection mismatch';\n"
        "    END IF;\nEND;\n$kt_backup_assert$;\nCOMMIT;\n"
    ).encode("ascii")


def restore_atomically(pg, directory, target, expected, schema_version):
    """Stream pg_restore's SQL through one psql transaction, including validation.

    pg_restore --single-transaction commits *before* the old post-restore
    manifest comparison. Feeding its SQL plus the comparison into one psql
    session means any SQL error OR projection mismatch rolls back all DDL/data.
    No huge dump is materialized in memory or on disk as a SQL intermediate.
    """
    options = pg.options()
    with (directory / DUMP).open("rb") as archive:
        reader = subprocess.Popen(
            pg.command(
                "pg_restore",
                ("--format=custom", "--no-owner", "--no-privileges", "--file=-"),
            ),
            stdin=archive, stdout=subprocess.PIPE, **options,
        )
        writer = None
        try:
            writer = subprocess.Popen(
                pg.command("psql", (*PSQL_ARGS, f"--dbname={target}")),
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, **options,
            )
            writer.stdin.write(b"BEGIN;\n")
            while chunk := reader.stdout.read(1024 * 1024):
                writer.stdin.write(chunk)
            pg.check(reader.wait(), "pg_restore")
            writer.stdin.write(restore_assertion_sql(expected, schema_version))
            writer.stdin.close()
            pg.check(writer.wait(), "psql")
        except OSError:
            # A broken pipe often means ON_ERROR_STOP terminated psql already.
            # Closing that transaction (without COMMIT) causes PostgreSQL rollback.
            raise BackupError("Restore stream failed; target transaction rolled back.") from None
        finally:
            reader.stdout.close()
            if reader.poll() is None:
                reader.kill()
            reader.wait()
            if writer is not None:
                if not writer.stdin.closed:
                    writer.stdin.close()
                if writer.poll() is None:
                    writer.kill()
                writer.wait()


def restore(pg, directory, target):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]{0,62}", target):
        raise BackupError(
            "Use a database name of up to 63 letters, digits, underscores or hyphens."
        )
    expected = verify_bundle(directory)
    version = json.loads((directory / MANIFEST).read_text(encoding="utf-8"))[
        "schema_version"
    ]
    pg.require_version("psql")
    pg.require_version("pg_restore")
    if pg.compose and pg.psql(b"SELECT current_database();").decode("utf-8") == target:
        raise BackupError("Choose a target other than the active Compose database.")
    pg.require_server(target)
    if pg.psql(EMPTY_DATABASE, target) != b"t":
        raise BackupError("Restore requires a freshly created empty database.")

    restore_atomically(pg, directory, target, expected, version)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--compose",
        action="store_true",
        help="Use PostgreSQL tools in Compose service db.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    create_parser = subparsers.add_parser(
        "create", help="Create a new backup bundle directory."
    )
    create_parser.add_argument("directory", type=Path)
    verify_parser = subparsers.add_parser(
        "verify", help="Verify the local bundle checksums and format."
    )
    verify_parser.add_argument("directory", type=Path)
    restore_parser = subparsers.add_parser(
        "restore", help="Restore and compare contents to the manifest."
    )
    restore_parser.add_argument("directory", type=Path)
    restore_parser.add_argument("--target-db", required=True)
    args = parser.parse_args()
    pg = Postgres(args.compose)

    try:
        if args.command == "create":
            create(pg, args.directory.resolve())
            print("Backup created and checksums verified.")
        elif args.command == "verify":
            verify_bundle(args.directory)
            print("Backup checksums and manifest format verified.")
        else:
            restore(pg, args.directory, args.target_db)
            print("Database restored and manifest collections matched.")
    except (BackupError, OSError, ValueError) as error:
        parser.exit(1, f"Backup error: {error}\n")


if __name__ == "__main__":
    main()
