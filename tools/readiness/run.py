"""Isolated PostgreSQL corpus/restore audit; never accepts a production DSN."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "apps/backend"), str(ROOT / "tools/backup")]


def safe_database(name):
    if not re.fullmatch(r"kt_readiness_[a-z0-9_]{1,40}", name):
        raise ValueError("Only a new kt_readiness_ database is permitted")
    return name


def safe_work(path):
    path = Path(path).resolve()
    if path == ROOT or ROOT in path.parents or path.exists():
        raise ValueError("Choose a new private work directory outside the repository")
    return path


def connection_args():
    # This is the separate local QA cluster, never the Windows serving cluster.
    if os.getenv("KT_READINESS_PORT", "62224") != "62224":
        raise ValueError("Only the isolated QA cluster on loopback:62224 is allowed")
    password = os.environ.get("KT_READINESS_PASSWORD")
    if not password:
        raise ValueError("KT_READINESS_PASSWORD is required")
    return {"host": "127.0.0.1", "port": 62224, "user": "kt_dev", "password": password}


def fingerprint(connect, database):
    import backup
    import psycopg
    from psycopg import sql

    result = {}
    with psycopg.connect(
        **connect, dbname=database, options="-c default_transaction_read_only=on"
    ) as db:
        for name, (table, _) in backup.COLLECTIONS.items():
            digest, count = hashlib.sha256(), 0
            with db.cursor(name="kt114_" + name) as rows:
                rows.execute(
                    sql.SQL("SELECT to_jsonb(t) FROM {} t ORDER BY id").format(
                        sql.Identifier(table)
                    )
                )
                for (row,) in rows:
                    digest.update(
                        json.dumps(
                            row,
                            sort_keys=True,
                            ensure_ascii=False,
                            separators=(",", ":"),
                        ).encode()
                    )
                    digest.update(b"\n")
                    count += 1
            result[name] = {"rows": count, "sha256": digest.hexdigest()}
    return result


def run(args, report):
    import psycopg
    from psycopg import sql

    connect = connection_args()
    work = safe_work(args.work_dir)
    run_id = datetime.now(UTC).strftime("%Y%m%d%H%M%S") + "_" + uuid4().hex[:8]
    source = safe_database("kt_readiness_" + run_id)
    target = safe_database(source + "_restore")
    work.mkdir(parents=True)
    receipt = {"run_id": run_id, "source": source, "target": target}
    (work / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
    report.update(stage="create_isolated_databases", run_id=run_id)
    with psycopg.connect(**connect, dbname="postgres", autocommit=True) as db:
        for name in (source, target):
            db.execute(
                sql.SQL("CREATE DATABASE {} TEMPLATE template0 ENCODING 'UTF8'").format(
                    sql.Identifier(name)
                )
            )
    os.environ.update(
        POSTGRES_DB=source,
        POSTGRES_USER=connect["user"],
        POSTGRES_PASSWORD=connect["password"],
        POSTGRES_HOST=connect["host"],
        POSTGRES_PORT=str(connect["port"]),
        DJANGO_SETTINGS_MODULE="config.settings",
        DJANGO_SECRET_KEY="kt114-isolated-test-only",
        LOCAL_ASR_MODEL_DIR="",
        PGDATABASE=source,
        PGUSER=connect["user"],
        PGPASSWORD=connect["password"],
        PGHOST=connect["host"],
        PGPORT=str(connect["port"]),
        PGCLIENTENCODING="UTF8",
    )
    import django

    django.setup()
    import backup
    from corpus import evaluate, seed
    from django.core.management import call_command
    from django.db import connections

    report["stage"] = "migrate_and_seed"
    call_command("migrate", interactive=False, verbosity=0)
    with connections["default"].cursor() as db:
        db.execute("CREATE TABLE kt_readiness_marker (run_id text PRIMARY KEY)")
        db.execute("INSERT INTO kt_readiness_marker VALUES (%s)", [run_id])
    seeded = seed(args.items)
    report["corpus"] = {
        "initial_items": args.items,
        "synthetic": True,
        "seed": "kt114-v1",
    }
    report["checks"] = evaluate(seeded, args.items)
    before = fingerprint(connect, source)
    report["stage"] = "backup_restore"
    bundle = work / "bundle"
    backup.create(backup.Postgres(False), bundle)
    backup.verify_bundle(bundle)
    backup.restore(backup.Postgres(False), bundle, target)
    after = fingerprint(connect, target)
    if before != after:
        raise ValueError("Full domain rows differ after restore")
    report["restoration"] = {
        "all_full_row_hashes_match": True,
        "includes_opaque_locators_metadata": True,
        "collections": before,
    }
    with psycopg.connect(
        **connect, dbname=target, options="-c default_transaction_read_only=on"
    ) as db:
        oauth, sessions = db.execute(
            "SELECT (SELECT count(*) FROM storage_driveaccount), (SELECT count(*) FROM django_session)"
        ).fetchone()
        if oauth or sessions:
            raise ValueError("Excluded identity rows were restored")
    payload = b"KT114 synthetic original: Ti\xe1\xba\xbfng Vi\xe1\xbb\x87t\r\n"
    (work / "sample-original.txt").write_bytes(payload)
    report["synthetic_original"] = {
        "local_bytes_readback": (work / "sample-original.txt").read_bytes() == payload,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "remote_readback": "NOT_RUN",
    }
    report["external_gates"] = {
        "hundred_gb_media": "NOT_RUN",
        "drive_large_file_quota": "NOT_RUN",
        "oauth_host_client_project_change": "NOT_RUN",
        "android_device": "NOT_RUN",
        "live_facebook_tiktok_youtube": "NOT_RUN",
        "native_mp4_playback": "NOT_RUN",
        "semantic_auto_group_precision": "NOT_RUN_NO_LABELLED_CORPUS",
    }
    report.update(
        status="PASS",
        stage="complete",
        scope="Synthetic PostgreSQL integrity/restore only; external gates remain open",
    )
    report["retained_databases"] = True


def cleanup(receipt_path):
    import psycopg
    from psycopg import sql

    receipt = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
    connect = connection_args()
    names = [safe_database(receipt[k]) for k in ("target", "source")]
    # Require a marker written by this run in EACH named DB. Never force sessions.
    for name in names:
        with psycopg.connect(
            **connect, dbname=name, options="-c default_transaction_read_only=on"
        ) as db:
            markers = db.execute("SELECT run_id FROM kt_readiness_marker").fetchall()
            if markers != [(receipt["run_id"],)]:
                raise ValueError("Fixture database marker mismatch")
    with psycopg.connect(**connect, dbname="postgres", autocommit=True) as db:
        for name in names:
            db.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(name)))
    print("Removed two marked isolated QA databases; private bundle retained")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--items", type=int, default=10_000)
    parser.add_argument(
        "--cleanup", type=Path, help="Receipt for two disposable marked QA databases"
    )
    args = parser.parse_args()
    if args.cleanup:
        cleanup(args.cleanup)
        return 0
    if not args.work_dir or not args.report or args.items != 10_000:
        parser.error(
            "--work-dir and --report are required; this gate uses exactly 10000 items"
        )
    report = {
        "status": "FAIL",
        "stage": "initialization",
        "checked_at": datetime.now(UTC).isoformat(),
        "code_sha": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
    }
    try:
        run(args, report)
    except Exception as error:  # noqa: BLE001 - redact credentials/source payloads
        report["error_type"] = type(error).__name__
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": report["status"], "stage": report["stage"]}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
