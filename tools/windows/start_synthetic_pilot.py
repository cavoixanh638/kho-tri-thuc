"""Serve the existing 36-note QA pilot on Windows, or remeasure it in Chromium."""

import argparse
import os
import secrets
import socket
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BACKEND = REPO / "apps" / "backend"
WEB = REPO / "apps" / "web"
EVAL = REPO / "evals" / "vietnamese-journeys"
PG = Path("C:/Program Files/PostgreSQL/18/bin")
HOST = "127.0.0.1"
WEB_PORT = 62310
DB_PORT = "56325"
DB_NAME = "kt_p08_journeys"
DB_USER = "kt_qa"


def run(command, **kwargs):
    return subprocess.run([str(arg) for arg in command], check=True, **kwargs)


def start(state, python):
    data = state / "pgdata"
    if data.resolve() != data or (data / "PG_VERSION").read_text().strip() != "18":
        raise SystemExit("Expected the existing PostgreSQL 18 QA cluster.")
    password = (state / "qa-password").read_text(encoding="utf-8-sig").strip()
    with socket.socket() as probe:
        try:
            probe.bind((HOST, WEB_PORT))
        except OSError as error:
            raise SystemExit(f"Could not bind {HOST}:{WEB_PORT}. The existing service was left running.") from error

    pg_ctl = PG / "pg_ctl.exe"
    status = subprocess.run([pg_ctl, "-D", data, "status"], capture_output=True)
    if status.returncode == 3:
        run([
            pg_ctl, "-D", data, "-w", "-t", "30", "start", "-l",
            state / "postgres.log", "-o", f"-h {HOST} -p {DB_PORT}",
        ])
    elif status.returncode != 0:
        raise SystemExit("Could not determine the PostgreSQL QA cluster status.")

    account = ["-h", HOST, "-p", DB_PORT, "-U", DB_USER, "-d", DB_NAME]
    identity = run(
        [PG / "psql.exe", "-XAtw", *account, "-c",
         "SELECT current_database(), inet_server_port(), current_setting('data_directory')"],
        env={**os.environ, "PGPASSWORD": password, "PGCONNECT_TIMEOUT": "3"},
        capture_output=True, text=True,
    ).stdout.strip().split("|", 2)
    if len(identity) != 3 or identity[:2] != [DB_NAME, DB_PORT] or Path(identity[2]).resolve() != data:
        raise SystemExit("Unexpected PostgreSQL QA cluster identity.")

    dist = state / "pilot-web-dist"
    if dist.resolve() != dist:
        raise SystemExit("The pilot build directory must be inside the QA state directory.")
    run(["npm.cmd", "run", "build", "--", "--outDir", dist], cwd=WEB)
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "config.settings",
        "DJANGO_SECRET_KEY": secrets.token_urlsafe(48),
        "DJANGO_DEBUG": "0",
        "DJANGO_ALLOWED_HOSTS": f"{HOST},localhost",
        "POSTGRES_DB": DB_NAME,
        "POSTGRES_HOST": HOST,
        "POSTGRES_PORT": DB_PORT,
        "POSTGRES_USER": DB_USER,
        "POSTGRES_PASSWORD": password,
        "WEB_DIST": str(dist),
        "UPLOAD_STAGING_ROOT": str(state / "pilot-staging"),
        "THUMBNAIL_CACHE_DIR": str(state / "pilot-thumbnails"),
        "GOOGLE_DRIVE_CLIENT_ID": "",
        "GOOGLE_DRIVE_CLIENT_SECRET": "",
        "GOOGLE_DRIVE_REDIRECT_URI": "",
        "GOOGLE_DRIVE_TOKEN_KEY": "",
        "GEMINI_API_KEY": "",
        "GEMINI_OCR_ENABLED": "0",
        "GEMINI_OCR_EXTERNAL_PROCESSING_ALLOWED": "0",
    }
    run([python, "manage.py", "migrate", "--check"], cwd=BACKEND, env=env)
    print(f"Pilot at http://{HOST}:{WEB_PORT}. Press Ctrl+C to stop the web server.", flush=True)
    run([python, "-m", "waitress", f"--listen={HOST}:{WEB_PORT}", "config.wsgi:application"],
        cwd=BACKEND, env=env)


def measure(state, chromium, *, navigation=False):
    credentials = {}
    for line in (state / "pilot-login.txt").read_text(encoding="utf-8-sig").splitlines():
        name, _, value = line.partition(":")
        if name in {"Username", "Password"}:
            credentials[name] = value.strip()
    if not credentials.get("Username") or not credentials.get("Password"):
        raise SystemExit("The pilot login file must contain Username and Password entries.")
    env = {
        **os.environ,
        "KT_EVAL_BROWSER_ORIGIN": f"http://{HOST}:{WEB_PORT}",
        "KT_EVAL_BROWSER_QA": "1",
        "KT_EVAL_BROWSER_SEED": str(state / "pilot-seed-map.json"),
        "KT_EVAL_BROWSER_USER": credentials["Username"],
        "KT_EVAL_BROWSER_PASSWORD": credentials["Password"],
        "KT_EVAL_BROWSER_CORRECTION": "verify",
        "KT_JOURNEY_CHROMIUM": str(chromium),
    }
    command = ["node", EVAL / "measure_browser.mjs"]
    if navigation:
        command.append("--navigation-only")
    run(command, cwd=REPO, env=env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, default=Path(tempfile.gettempdir()) / "ktt-rc25-qa")
    parser.add_argument("--python", type=Path, default=Path(os.environ["LOCALAPPDATA"]) /
                        "KhoTriThuc" / "venv" / "Scripts" / "python.exe")
    parser.add_argument("--chromium", type=Path, default=Path(
        "C:/Program Files/Google/Chrome/Application/chrome.exe"))
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--measure", action="store_true", help="Remeasure the running pilot in Chromium.")
    modes.add_argument("--measure-navigation", action="store_true",
                       help="Check search filters and browser history on the running pilot.")
    args = parser.parse_args()
    state = args.state.resolve(strict=True)
    if state.name.casefold() != "ktt-rc25-qa" or not all(
        (state / name).is_file() for name in ("qa-password", "pilot-login.txt", "pilot-seed-map.json")
    ):
        parser.error("Choose the existing ktt-rc25-qa directory with its pilot files.")
    if args.measure or args.measure_navigation:
        measure(state, args.chromium, navigation=args.measure_navigation)
    else:
        start(state, args.python.resolve(strict=True))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit(130) from None
