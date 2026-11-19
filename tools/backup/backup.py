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
SCHEMA_VERSION = 3
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


def manifest_query(names=None, schema_version=SCHEMA_VERSION):
    parts = []
    for name, (table, columns) in COLLECTIONS.items():
        if names is not None and name not in names:
            continue
        if name == "topics" and schema_version < 3:
            columns = "id, owner_id, name, parent_id, archived"
        parts.append(
            f"'{name}', (SELECT COALESCE(json_agg(r ORDER BY r.id), '[]'::json) "
            f"FROM (SELECT {columns} FROM public.{table}) r)"
        )
    return (
        "SELECT json_build_object(\n" + ",\n".join(parts) + "\n);\nCOMMIT;\n"
    ).encode()


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
        or manifest["schema_version"] not in (1, 2, SCHEMA_VERSION)
        or manifest.get("postgres_major") != PG_MAJOR
    ):
        raise BackupError("Unsupported backup manifest format.")
    collections = manifest.get("collections")
    if (
        not isinstance(collections, dict)
        or set(collections)
        != (
            set(COLLECTIONS)
            if manifest["schema_version"] >= 2
            else set(COLLECTIONS) - {"knowledge_exports"}
        )
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

    # A pathless pg_restore reads its archive on stdin, including through Compose.
    with (directory / DUMP).open("rb") as archive:
        pg.run(
            "pg_restore",
            "--single-transaction",
            "--exit-on-error",
            "--no-password",
            "--no-owner",
            "--no-privileges",
            f"--dbname={target}",
            stdin=archive,
            output=subprocess.DEVNULL,
        )

    actual = json.loads(
        pg.psql(TRANSACTION + manifest_query(expected, version), target)
    )
    if actual != expected:
        mismatches = ", ".join(
            name for name in expected if actual[name] != expected[name]
        )
        raise BackupError(
            f"Restore contents differ from the manifest in: {mismatches}."
        )


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
