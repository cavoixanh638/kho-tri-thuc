"""Run the GitHub checkout locally with an isolated PostgreSQL 18 cluster."""

import argparse
import base64
import json
import os
import secrets
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

REPOSITORY = Path(__file__).resolve().parents[2]
BACKEND = REPOSITORY / "apps" / "backend"
WEB = REPOSITORY / "apps" / "web"
ROOT = Path(os.environ["LOCALAPPDATA"]) / "KhoTriThuc"
STATE = ROOT / "runtime"
CONFIG = STATE / "config.json"
PG_BIN = Path("C:/Program Files/PostgreSQL/18/bin")
CREATE_FLAGS = subprocess.CREATE_NO_WINDOW


def run(command, *, cwd=None, env=None):
    subprocess.run([str(part) for part in command], cwd=cwd, env=env, check=True)


def python_path():
    return ROOT / "venv" / "Scripts" / "python.exe"


def pg(name):
    binary = PG_BIN / (name + ".exe")
    if not binary.is_file():
        raise RuntimeError("PostgreSQL 18 binaries were not found.")
    return binary


def load_config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def runtime_env(config):
    env = os.environ.copy()
    env.update(config["environment"])
    env["PYTHONUTF8"] = "1"
    env["PYTHONUNBUFFERED"] = "1"
    return env


def manage(config, *args, extra_env=None):
    env = runtime_env(config)
    if extra_env:
        env.update(extra_env)
    run([python_path(), "manage.py", *args], cwd=BACKEND, env=env)


def database_started():
    if not (STATE / "pgdata").is_dir():
        return False
    result = subprocess.run(
        [pg("pg_ctl"), "-D", STATE / "pgdata", "status"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=CREATE_FLAGS,
    )
    return result.returncode == 0


def start_database(config):
    if not database_started():
        run(
            [
                pg("pg_ctl"),
                "-D",
                STATE / "pgdata",
                "-w",
                "-t",
                "30",
                "start",
                "-l",
                STATE / "postgres.log",
                "-o",
                f"-h 127.0.0.1 -p {config['environment']['POSTGRES_PORT']}",
            ]
        )


def setup():
    if not ROOT.exists():
        ROOT.mkdir(parents=True)
    owner = subprocess.check_output(["whoami"], text=True).strip()
    run(["icacls", ROOT, "/inheritance:r", "/grant:r", f"{owner}:(OI)(CI)F"])
    STATE.mkdir(exist_ok=True)
    for name in ("staging", "thumbnails"):
        (STATE / name).mkdir(exist_ok=True)

    if not CONFIG.exists():
        password = secrets.token_urlsafe(32)
        config = {
            "environment": {
                "DJANGO_SECRET_KEY": secrets.token_urlsafe(48),
                "DJANGO_DEBUG": "0",
                "DJANGO_ALLOWED_HOSTS": "127.0.0.1,localhost",
                "POSTGRES_DB": "kho_tri_thuc",
                "POSTGRES_USER": "kt_owner",
                "POSTGRES_PASSWORD": password,
                "POSTGRES_HOST": "127.0.0.1",
                "POSTGRES_PORT": "54329",
                "UPLOAD_STAGING_ROOT": str(STATE / "staging"),
                "THUMBNAIL_CACHE_DIR": str(STATE / "thumbnails"),
                "WEB_DIST": str(WEB / "dist"),
                "GOOGLE_DRIVE_TOKEN_KEY": base64.urlsafe_b64encode(
                    secrets.token_bytes(32)
                ).decode(),
                "GOOGLE_DRIVE_REDIRECT_URI": "http://127.0.0.1:8009/api/v1/integrations/drive/callback",
            },
            "http_port": 8009,
        }
        CONFIG.write_text(json.dumps(config, indent=2), encoding="utf-8")
    config = load_config()

    if not python_path().is_file():
        run([sys.executable, "-m", "venv", ROOT / "venv"])
    run(
        [
            python_path(),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "-r",
            BACKEND / "requirements.txt",
        ]
    )
    run(["npm.cmd", "ci", "--no-audit", "--no-fund"], cwd=WEB)
    run(["npm.cmd", "run", "build"], cwd=WEB)

    if not (STATE / "pgdata" / "PG_VERSION").is_file():
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", int(config["environment"]["POSTGRES_PORT"])))
        pwfile = STATE / "bootstrap-password"
        try:
            pwfile.write_text(
                config["environment"]["POSTGRES_PASSWORD"], encoding="utf-8"
            )
            run(
                [
                    pg("initdb"),
                    "-D",
                    STATE / "pgdata",
                    "-U",
                    "kt_owner",
                    "--encoding=UTF8",
                    "--no-locale",
                    "--auth=scram-sha-256",
                    "--pwfile",
                    pwfile,
                ]
            )
        finally:
            pwfile.unlink(missing_ok=True)
    start_database(config)
    env = runtime_env(config)
    env["PGPASSWORD"] = config["environment"]["POSTGRES_PASSWORD"]
    database_exists = subprocess.check_output(
        [
            pg("psql"),
            "-h",
            "127.0.0.1",
            "-p",
            env["POSTGRES_PORT"],
            "-U",
            "kt_owner",
            "-d",
            "postgres",
            "-At",
            "-c",
            "SELECT 1 FROM pg_database WHERE datname='kho_tri_thuc'",
        ],
        env=env,
        text=True,
    ).strip()
    if database_exists != "1":
        run(
            [
                pg("createdb"),
                "-h",
                "127.0.0.1",
                "-p",
                env["POSTGRES_PORT"],
                "-U",
                "kt_owner",
                "--encoding=UTF8",
                "--template=template0",
                "kho_tri_thuc",
            ],
            env=env,
        )
    manage(config, "migrate", "--noinput")
    manage(config, "check", "--database", "default")
    if not (STATE / "initial-login.txt").exists():
        password = config.setdefault(
            "initial_admin_password", secrets.token_urlsafe(18)
        )
        CONFIG.write_text(json.dumps(config, indent=2), encoding="utf-8")
        manage(
            config,
            "createsuperuser",
            "--noinput",
            "--username",
            "admin",
            "--email",
            "",
            extra_env={"DJANGO_SUPERUSER_PASSWORD": password},
        )
        (STATE / "initial-login.txt").write_text(
            f"URL http://127.0.0.1:8009\nUsername admin\nPassword {password}\n",
            encoding="utf-8",
        )
    if "initial_admin_password" in config:
        del config["initial_admin_password"]
        CONFIG.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print("Setup completed. The initial login is in the private runtime directory.")


def configure_drive(client_file):
    if client_file is None or client_file.stat().st_size > 64 * 1024:
        raise ValueError("Choose the downloaded Google Web OAuth client JSON.")
    payload = json.loads(client_file.read_text(encoding="utf-8"))
    web = payload.get("web", {})
    config = load_config()
    redirect = config["environment"]["GOOGLE_DRIVE_REDIRECT_URI"]
    if redirect not in web.get("redirect_uris", []):
        raise ValueError(
            "Register the application's exact redirect URI in this OAuth client."
        )
    client_id = web.get("client_id")
    client_secret = web.get("client_secret")
    if not (
        isinstance(client_id, str)
        and client_id.endswith(".apps.googleusercontent.com")
        and isinstance(client_secret, str)
        and 0 < len(client_secret) <= 4096
    ):
        raise ValueError(
            "The JSON must contain a Google Web OAuth client ID and client secret."
        )
    config["environment"].update(
        {
            "GOOGLE_DRIVE_CLIENT_ID": client_id,
            "GOOGLE_DRIVE_CLIENT_SECRET": client_secret,
        }
    )
    pending = CONFIG.with_suffix(".pending")
    pending.write_text(json.dumps(config, indent=2), encoding="utf-8")
    pending.replace(CONFIG)
    print(
        "Google Drive client configured locally. Restart the API and worker, then connect in Settings."
    )


def start():
    config = load_config()
    start_database(config)
    env = runtime_env(config)
    processes = []
    state_file = STATE / "processes.json"
    if state_file.exists():
        try:
            with urlopen(
                f"http://127.0.0.1:{config['http_port']}/api/v1/health", timeout=2
            ) as response:
                if response.status == 200:
                    print("Application is already running.")
                    return
        except OSError:
            pass
        raise RuntimeError(
            "Saved process state exists. Run status/stop before restarting."
        )
    for name, args in [
        (
            "api",
            [
                "-m",
                "waitress",
                "--listen=127.0.0.1:" + str(config["http_port"]),
                "--threads=8",
                "--max-request-body-size=135266304",
                "config.wsgi:application",
            ],
        ),
        ("worker", ["manage.py", "run_worker"]),
    ]:
        with (STATE / (name + ".log")).open("ab") as output:
            process = subprocess.Popen(
                [str(python_path()), *args],
                cwd=BACKEND,
                env=env,
                stdout=output,
                stderr=subprocess.STDOUT,
                creationflags=CREATE_FLAGS,
            )
        processes.append({"name": name, "pid": process.pid})
    state_file.write_text(json.dumps(processes), encoding="utf-8")
    for _ in range(40):
        try:
            with urlopen(
                f"http://127.0.0.1:{config['http_port']}/api/v1/health", timeout=2
            ) as response:
                if response.status == 200:
                    print(
                        f"Application ready at http://127.0.0.1:{config['http_port']}"
                    )
                    return
        except OSError:
            time.sleep(0.5)
    raise RuntimeError("Application did not become ready. Check the private API log.")


def status():
    config = load_config()
    try:
        with urlopen(
            f"http://127.0.0.1:{config['http_port']}/api/v1/health", timeout=3
        ) as response:
            print("API", response.status)
    except OSError:
        print("API unavailable")
    print("PostgreSQL", "running" if database_started() else "stopped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action", choices=["setup", "start", "status", "configure-drive"]
    )
    parser.add_argument("--client-file", type=Path)
    args = parser.parse_args()
    if args.action == "configure-drive":
        configure_drive(args.client_file)
    else:
        {"setup": setup, "start": start, "status": status}[args.action]()
