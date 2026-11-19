"""Private child entrypoint. No Django configuration or credentials are loaded."""

import contextlib
import ipaddress
import json
import math
import os
import re
import socket
import sys
from pathlib import Path
from urllib.parse import urlsplit

MAX_BYTES = 128 * 1024 * 1024
ALLOWED_DOMAINS = ("facebook.com", "fbcdn.net", "fbsbx.com")
GLOBAL_V6 = ipaddress.ip_network("2000::/3")


class DownloadBlocked(OSError):
    pass


def allowed_host(host):
    if not isinstance(host, str) or not host or host.endswith("."):
        return False
    host = host.lower()
    return any(
        host == domain or host.endswith("." + domain) for domain in ALLOWED_DOMAINS
    )


def public_ip(address):
    try:
        ip = ipaddress.ip_address(address)
        if isinstance(ip, ipaddress.IPv6Address) and (
            ip not in GLOBAL_V6 or ip.ipv4_mapped or ip.sixtofour or ip.teredo
        ):
            return False
        return (
            ip.is_global
            and not ip.is_multicast
            and not getattr(ip, "ipv4_mapped", None)
        )
    except ValueError:
        return False


def install_network_guard():
    original_resolve = socket.getaddrinfo
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    approved = set()

    def resolve(host, port, *args, **kwargs):
        if port not in (443, "443", "https") or not (
            allowed_host(host) or host in approved
        ):
            raise DownloadBlocked("video_network_blocked")
        records = original_resolve(host, port, *args, **kwargs)
        if not records or any(not public_ip(record[4][0]) for record in records):
            raise DownloadBlocked("video_network_blocked")
        approved.update(record[4][0] for record in records)
        return records

    def check_address(address):
        if (
            not isinstance(address, tuple)
            or len(address) < 2
            or address[1] != 443
            or address[0] not in approved
            or not public_ip(address[0])
        ):
            raise DownloadBlocked("video_network_blocked")

    def connect(sock, address):
        check_address(address)
        return original_connect(sock, address)

    def connect_ex(sock, address):
        check_address(address)
        return original_connect_ex(sock, address)

    socket.getaddrinfo = resolve
    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex


class BoundedWriter:
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        if self.stream.tell() + len(data) > MAX_BYTES:
            raise DownloadBlocked("video_too_large")
        return self.stream.write(data)

    def __getattr__(self, name):
        return getattr(self.stream, name)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return self.stream.__exit__(*args)


def install_file_guard(directory, downloader_class):
    original = downloader_class.sanitize_open

    def bounded_open(instance, filename, mode):
        path = Path(filename).absolute()
        if (
            path.parent != directory
            or path.name not in {"video.mp4", "video.mp4.part"}
            or mode != "wb"
        ):
            raise DownloadBlocked("video_invalid_output")
        stream, name = original(instance, filename, mode)
        return BoundedWriter(stream), name

    downloader_class.sanitize_open = bounded_open


def select_progressive(context):
    formats = context.get("formats", [])
    for format_id in ("hd", "sd"):
        for candidate in formats:
            parts = urlsplit(candidate.get("url", ""))
            if (
                candidate.get("format_id") == format_id
                and candidate.get("ext") == "mp4"
                and candidate.get("acodec") != "none"
                and candidate.get("vcodec") != "none"
                and parts.scheme == "https"
                and parts.port in (None, 443)
                and not parts.username
                and not parts.password
                and allowed_host(parts.hostname)
                and not candidate.get("fragments")
                and candidate.get("protocol") in (None, "https", "http")
            ):
                yield candidate
                return
    raise DownloadBlocked("video_progressive_unavailable")


class Quiet:
    def debug(self, _message):
        pass

    def warning(self, _message):
        pass

    def error(self, _message):
        pass


def clean_text(text, limit):
    return (
        str(text or "")
        .replace("\x00", "")
        .encode("utf-8", errors="replace")
        .decode()[:limit]
    )


def run(url, directory):
    install_network_guard()
    import yt_dlp
    from yt_dlp.downloader.common import FileDownloader
    from yt_dlp.globals import plugin_dirs

    plugin_dirs.value = []
    install_file_guard(directory, FileDownloader)
    options = {
        "quiet": True,
        "noprogress": True,
        "logger": Quiet(),
        "noplaylist": True,
        "playlist_items": "1",
        "allowed_extractors": ["facebook.*", "generic"],
        "cachedir": False,
        "outtmpl": str(directory / "video.mp4"),
        "format": select_progressive,
        "socket_timeout": 15,
        "retries": 0,
        "extractor_retries": 0,
        "fragment_retries": 0,
        "file_access_retries": 0,
        "max_filesize": MAX_BYTES,
        "buffersize": 64 * 1024,
        "noresizebuffer": True,
        "continuedl": False,
        "nopart": False,
        "proxy": "",
        "nocheckcertificate": False,
        "enable_file_urls": False,
        "writeinfojson": False,
        "writethumbnail": False,
        "writesubtitles": False,
        "writeautomaticsub": False,
        "writedescription": False,
        "fixup": "never",
        "postprocessors": [],
        "remote_components": set(),
        "js_runtimes": {},
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(options) as tool:
        info = tool.extract_info(url, download=True)
    if not isinstance(info, dict) or info.get("_type", "video") != "video":
        raise DownloadBlocked("video_unavailable")
    platform_id = str(info.get("id", ""))
    if not re.fullmatch(r"[0-9]{1,64}", platform_id):
        raise DownloadBlocked("video_unavailable")
    duration = info.get("duration")
    if (
        not isinstance(duration, (int, float))
        or isinstance(duration, bool)
        or not math.isfinite(duration)
    ):
        duration = None
    return {
        "status": "done",
        "title": clean_text(info.get("title"), 512),
        "description": clean_text(info.get("description"), 2048),
        "platform_id": platform_id,
        "duration": duration,
    }


def main():
    directory = Path(sys.argv[2]).absolute()
    result = {"status": "failed", "error_code": "video_unavailable"}
    try:
        # Extractors must never print signed media URLs or account details.
        with (
            open(os.devnull, "w") as sink,
            contextlib.redirect_stdout(sink),
            contextlib.redirect_stderr(sink),
        ):
            result = run(sys.argv[1], directory)
    except ImportError:
        result["error_code"] = "video_dependency_missing"
    except Exception as error:  # noqa: BLE001 - never expose extractor exception URLs
        message = str(error)
        for code in (
            "video_network_blocked",
            "video_too_large",
            "video_progressive_unavailable",
        ):
            if code in message:
                result["error_code"] = code
                break
    (directory / "result.json").write_text(
        json.dumps(result, ensure_ascii=True), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
