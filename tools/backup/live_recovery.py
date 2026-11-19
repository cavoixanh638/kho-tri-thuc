"""Audit a native Windows backup through Drive and a new disposable database.

Runtime configuration, dump, archive, Drive receipts and downloaded originals
stay in the private work directory. Only the explicit report is sanitized.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import backup
from drive_bundle import DriveBackups, digest, download, pack, unpack


@contextmanager
def environment(values):
    previous = {key: os.environ.get(key) for key in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _native_pg(config):
    values = config["environment"]
    return {
        "PGHOST": values["POSTGRES_HOST"],
        "PGPORT": values["POSTGRES_PORT"],
        "PGUSER": values["POSTGRES_USER"],
        "PGPASSWORD": values["POSTGRES_PASSWORD"],
        "PGDATABASE": values["POSTGRES_DB"],
        "PGOPTIONS": "-c default_transaction_read_only=on",
    }


def audit(args, report):
    if not re.fullmatch(r"kt_recovery_[a-z0-9_]{1,45}", args.target_db):
        raise backup.BackupError("Choose a new database with the kt_recovery_ prefix.")
    args.work_dir.mkdir(parents=True, exist_ok=False)
    config = json.loads(args.runtime_config.read_text(encoding="utf-8"))
    source_pg = _native_pg(config)
    pg_bin = Path(args.pg_bin)
    app_env = {
        **config["environment"],
        **source_pg,
        "PYTHONUTF8": "1",
        "PATH": str(pg_bin) + os.pathsep + os.environ["PATH"],
        "DJANGO_SETTINGS_MODULE": "config.settings",
    }
    report["stage"] = "source_snapshot"
    with environment(app_env):
        pg = backup.Postgres(False)
        bundle = args.work_dir / "source-bundle"
        backup.create(pg, bundle)
        collections = backup.verify_bundle(bundle)
        copy = args.work_dir / "independent-local-copy"
        shutil.copytree(bundle, copy)
        if backup.verify_bundle(copy) != collections:
            raise backup.BackupError("Independent local copy verification failed.")
        archive = args.work_dir / "backup.zip"
        sha256 = pack(bundle, archive)
        report.update(
            consistent_snapshot=True,
            independent_local_copy_verified=True,
            local_copy_scope="same Windows machine, outside Drive sync",
            archive_sha256=sha256,
            archive_bytes=archive.stat().st_size,
            dump_sha256=digest(bundle / backup.DUMP),
            manifest_sha256=digest(bundle / backup.MANIFEST),
            collection_counts={name: len(rows) for name, rows in collections.items()},
        )

        sys.path.insert(0, str(backup.ROOT / "apps" / "backend"))
        import django

        django.setup()
        from django.contrib.auth import get_user_model
        from django.db import connections, transaction
        from storage.drive import DriveClient, drive_credentials
        from storage.models import Asset, DriveAccount
        from storage.oauth import token_cipher
        from storage.service import DriveStorage

        owner = get_user_model().objects.get(username=args.owner)
        account = DriveAccount.objects.get(
            owner=owner, state=DriveAccount.State.CONNECTED
        )
        refresh = (
            token_cipher().decrypt(account.refresh_token_ciphertext.encode()).decode()
        )
        # No reauthorize callback: this auditor cannot mutate the source database.
        client = DriveClient(drive_credentials(refresh))
        report["stage"] = "drive_upload"
        backups = DriveBackups(
            client, account.root_folder_id, args.work_dir / "private-receipts"
        )
        file_id = backups.upload(archive)
        if backups.upload(archive) != file_id:
            raise backup.BackupError("Backup retry changed the Drive file identity.")
        report["backup_retry_same_file"] = True
        fetched = args.work_dir / "downloaded-backup.zip"
        download(client, file_id, fetched, archive.stat().st_size, sha256)
        recovered = args.work_dir / "downloaded-bundle"
        unpack(fetched, recovered)
        report["drive_backup_exact_readback"] = True

        target_pg = {
            "PGHOST": args.audit_host,
            "PGPORT": str(args.audit_port),
            "PGUSER": args.audit_user,
            "PGPASSWORD": os.getenv("KT_BACKUP_AUDIT_PASSWORD", ""),
            "PGDATABASE": "postgres",
            "PGOPTIONS": "",
        }
        if (source_pg["PGHOST"], source_pg["PGPORT"], source_pg["PGDATABASE"]) == (
            target_pg["PGHOST"],
            target_pg["PGPORT"],
            args.target_db,
        ):
            raise backup.BackupError(
                "The source database cannot be the restore target."
            )
        report["stage"] = "fresh_database_restore"
        with environment(target_pg):
            created = subprocess.run(
                [
                    str(pg_bin / "createdb.exe"),
                    "--no-password",
                    "--maintenance-db=postgres",
                    "--template=template0",
                    "--encoding=UTF8",
                    args.target_db,
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
                check=False,
            )
            if created.returncode:
                raise backup.BackupError("Fresh audit database creation failed.")
            backup.restore(pg, recovered, args.target_db)
            absent = json.loads(
                pg.psql(
                    b"SELECT json_build_object('oauth', (SELECT count(*) FROM storage_driveaccount), "
                    b"'sessions', (SELECT count(*) FROM django_session));",
                    args.target_db,
                )
            )
            if absent != {"oauth": 0, "sessions": 0}:
                raise backup.BackupError(
                    "Restored database contains excluded identity rows."
                )
            report.update(
                all_manifest_collections_exact=True,
                manifest_collection_count=len(collections),
                oauth_rows_restored=0,
                sessions_restored=0,
            )

        alias = "live_recovery_audit"
        connections.databases[alias] = {
            **connections.databases["default"],
            "NAME": args.target_db,
            "HOST": args.audit_host,
            "PORT": str(args.audit_port),
            "USER": args.audit_user,
            "PASSWORD": target_pg["PGPASSWORD"],
            "OPTIONS": {
                "connect_timeout": 3,
                "options": "-c default_transaction_read_only=off",
            },
        }
        report["stage"] = "restored_mapping_original_readback"
        originals = (
            Asset.objects.using(alias)
            .select_related("item")
            .filter(
                role="original",
                item__owner_id=owner.pk,
                locations__provider="google_drive",
                locations__status="verified",
            )
            .distinct()
        )
        verified = []
        for asset in originals:
            store = DriveStorage(client, account)
            # The real open() adapter updates verification time. Roll that update
            # back in the disposable DB so the restored snapshot remains exact.
            with transaction.atomic(using=alias):
                url = store.open(asset)
                if not url.startswith("https://drive.google.com/open?"):
                    raise backup.BackupError(
                        "Restored original mapping could not be opened."
                    )
                remote = store.stat(asset)
                transaction.set_rollback(True, using=alias)
            original = args.work_dir / ("original-readback-" + asset.pk.hex)
            try:
                download(client, remote.file_id, original, asset.size, asset.sha256)
                verified.append(
                    {
                        "bytes": asset.size,
                        "sha256": asset.sha256,
                        "exact_readback": True,
                        "adapter_open": True,
                    }
                )
            finally:
                original.unlink(missing_ok=True)
        if not verified:
            raise backup.BackupError(
                "No verified original was available for the live recovery audit."
            )
        report.update(
            restored_originals=verified,
            live_nonempty_group_assignments=any(
                collections[name]
                for name in (
                    "item_topics",
                    "item_projects",
                    "item_tags",
                )
            ),
            live_nonempty_notes=any(row["note"] for row in collections["items"]),
        )
        with environment(target_pg):
            actual = json.loads(
                pg.psql(backup.TRANSACTION + backup.manifest_query(), args.target_db)
            )
            if actual != collections:
                raise backup.BackupError(
                    "Restored rows changed during original readback audit."
                )
        connections[alias].close()
        report.update(
            status="PASS",
            stage="complete",
            production_database_read_only=True,
            same_oauth_client_and_project=True,
            different_client_project_tested=False,
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-config", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--owner", default="admin")
    parser.add_argument("--target-db", default="kt_recovery_" + uuid4().hex)
    parser.add_argument("--audit-host", default="127.0.0.1")
    parser.add_argument("--audit-port", type=int, default=62224)
    parser.add_argument("--audit-user", default="kt_dev")
    parser.add_argument("--pg-bin", default="C:/Program Files/PostgreSQL/18/bin")
    args = parser.parse_args()
    report = {"checked_at": datetime.now(UTC).isoformat(), "status": "FAIL"}
    try:
        audit(args, report)
    except Exception as error:  # noqa: BLE001 - redact DB, OAuth and remote exception details
        report["error_type"] = type(error).__name__
        if isinstance(error, backup.BackupError):
            report["error_reason"] = str(error)
        code = getattr(error, "code", "")
        if isinstance(code, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,63}", code):
            report["error_code"] = code
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "Live recovery audit",
        report["status"],
        "at stage",
        report.get("stage", "initialization"),
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
