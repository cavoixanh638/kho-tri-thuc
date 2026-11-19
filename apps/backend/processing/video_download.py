"""Bounded public Facebook MP4 download in a credential-free child process."""

import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

MAX_BYTES = 128 * 1024 * 1024
TIMEOUT_SECONDS = 120
MAX_RESULT_BYTES = 16 * 1024
FACEBOOK_HOSTS = {"facebook.com", "www.facebook.com", "m.facebook.com"}


class VideoDownloadError(Exception):
    def __init__(self, code, retryable=False):
        super().__init__(code)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True, slots=True)
class VideoResult:
    path: Path
    title: str = ""
    description: str = ""
    platform_id: str = ""
    duration: float | None = None


def is_facebook_url(url):
    if (
        not isinstance(url, str)
        or len(url) > 2048
        or re.search(r"[\s\\\x00-\x1f\x7f]", url)
    ):
        return False
    try:
        parts = urlsplit(url)
        if (
            parts.scheme != "https"
            or parts.netloc not in FACEBOOK_HOSTS
            or parts.fragment
            or parts.username
            or parts.password
            or parts.port is not None
        ):
            return False
        if re.fullmatch(r"/share/r/[A-Za-z0-9]+/?", parts.path):
            return not parts.query
        if re.fullmatch(r"/reel/[0-9]+/?", parts.path):
            return not parts.query
        query = parse_qs(parts.query, strict_parsing=True)
        return (
            parts.path in {"/watch", "/watch/"}
            and set(query) == {"v"}
            and len(query["v"]) == 1
            and bool(re.fullmatch(r"[0-9]+", query["v"][0]))
        )
    except ValueError:
        return False


def child_environment():
    # Explicit allowlist rather than deleting selected credential variable names.
    keep = {"SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "LANG", "LC_ALL"}
    env = {key: value for key, value in os.environ.items() if key.upper() in keep}
    env.update(PYTHONUTF8="1", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1")
    return env


def _directory_size(directory):
    total = 0
    for entry in directory.iterdir():
        if entry.is_symlink() or not entry.is_file():
            raise VideoDownloadError("video_invalid_output")
        total += entry.stat().st_size
    return total


def _wait(process, directory):
    deadline = time.monotonic() + TIMEOUT_SECONDS
    try:
        while process.poll() is None:
            if time.monotonic() >= deadline:
                raise VideoDownloadError("video_timeout", retryable=True)
            if _directory_size(directory) > MAX_BYTES + MAX_RESULT_BYTES:
                raise VideoDownloadError("video_too_large")
            time.sleep(0.05)
        if _directory_size(directory) > MAX_BYTES + MAX_RESULT_BYTES:
            raise VideoDownloadError("video_too_large")
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)


def _result(directory):
    manifest = directory / "result.json"
    if not manifest.is_file() or manifest.stat().st_size > MAX_RESULT_BYTES:
        raise VideoDownloadError("video_download_failed", retryable=True)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise VideoDownloadError("video_invalid_output")
    if data.get("status") != "done":
        codes = {
            "video_network_blocked",
            "video_too_large",
            "video_progressive_unavailable",
            "video_unavailable",
            "video_timeout",
            "video_dependency_missing",
        }
        code = data.get("error_code")
        raise VideoDownloadError(
            code if code in codes else "video_download_failed",
            retryable=code == "video_timeout",
        )
    path = directory / "video.mp4"
    if not path.is_file() or not 0 < path.stat().st_size <= MAX_BYTES:
        raise VideoDownloadError("video_invalid_output")
    with path.open("rb") as stream:
        header = stream.read(12)
    if len(header) < 12 or header[4:8] != b"ftyp":
        raise VideoDownloadError("video_invalid_output")
    for key, limit in (("title", 512), ("description", 2048), ("platform_id", 64)):
        if (
            not isinstance(data.get(key), str)
            or len(data[key]) > limit
            or "\x00" in data[key]
        ):
            raise VideoDownloadError("video_invalid_output")
    if not re.fullmatch(r"[0-9]+", data["platform_id"]):
        raise VideoDownloadError("video_invalid_output")
    duration = data.get("duration")
    if duration is not None and (
        isinstance(duration, bool)
        or not isinstance(duration, (float, int))
        or not math.isfinite(duration)
        or not 0 <= duration <= 24 * 3600
    ):
        raise VideoDownloadError("video_invalid_output")
    return VideoResult(
        path, data["title"], data["description"], data["platform_id"], duration
    )


def download_facebook(url, destination):
    if not is_facebook_url(url):
        raise VideoDownloadError("video_unsupported_url")
    destination = Path(destination).absolute()
    if destination.exists() or destination.is_symlink():
        raise VideoDownloadError("video_destination_exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    child = Path(__file__).with_name("video_download_child.py")
    try:
        with tempfile.TemporaryDirectory(
            prefix=".kt-video-", dir=destination.parent
        ) as temp:
            directory = Path(temp)
            with subprocess.Popen(
                [sys.executable, "-I", str(child), url, str(directory)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=directory,
                env=child_environment(),
                creationflags=subprocess.CREATE_NO_WINDOW
                if sys.platform == "win32"
                else 0,
            ) as process:
                _wait(process, directory)
            result = _result(directory)
            # Same-volume hard link atomically refuses overwriting a concurrent stage.
            os.link(result.path, destination)
            return VideoResult(
                destination,
                result.title,
                result.description,
                result.platform_id,
                result.duration,
            )
    except VideoDownloadError:
        raise
    except (OSError, ValueError, subprocess.SubprocessError):
        raise VideoDownloadError("video_download_failed", retryable=True) from None
