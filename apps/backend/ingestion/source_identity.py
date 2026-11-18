import ipaddress
import re
from dataclasses import dataclass
from hashlib import sha256
from urllib.parse import parse_qs, urlsplit


class UnsafeCaptureURL(ValueError):
    pass


@dataclass(frozen=True)
class SourceIdentity:
    canonical_url: str
    platform: str = "web"
    platform_id: str = ""

    @property
    def identity_hash(self):
        return sha256(self.canonical_url.encode("utf-8")).hexdigest()


_DNS_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")
_NUMERIC_LABEL = re.compile(r"[0-9]+|0x[0-9a-f]+")
_LOCAL_SUFFIXES = (".localhost", ".local", ".internal", ".home.arpa")
_YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com"}
_YOUTUBE_TRACKING = {
    "si",
    "feature",
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "utm_term",
}
_YOUTUBE_ID = re.compile(r"[A-Za-z0-9_-]{11}")


def _require_public_hostname(hostname):
    if "%" in hostname:
        raise UnsafeCaptureURL

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        dns = hostname.encode("idna").decode("ascii").lower().removesuffix(".")
        labels = dns.split(".")
        if (
            len(dns) > 253
            or len(labels) < 2
            or not all(_DNS_LABEL.fullmatch(label) for label in labels)
            or _NUMERIC_LABEL.fullmatch(labels[-1])
            or ("." + dns).endswith(_LOCAL_SUFFIXES)
        ):
            raise UnsafeCaptureURL from None
        return

    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
        address = address.ipv4_mapped
    if not address.is_global or address.is_multicast or address.is_reserved:
        raise UnsafeCaptureURL


def _youtube_id(parsed, suffix, port):
    if parsed.scheme != "https" or port not in (None, 443) or "#" in suffix:
        return ""
    if parsed.hostname != "youtu.be" and parsed.hostname not in _YOUTUBE_HOSTS:
        return ""

    path = parsed.path.split("/")
    query = parse_qs(parsed.query, keep_blank_values=True)
    if parsed.hostname == "youtu.be" and len(path) == 2:
        candidate = path[1]
    elif parsed.hostname in _YOUTUBE_HOSTS and parsed.path == "/watch":
        values = query.pop("v", [])
        candidate = values[0] if len(values) == 1 else ""
    elif (
        parsed.hostname in _YOUTUBE_HOSTS
        and len(path) == 3
        and path[1] in {"shorts", "embed"}
    ):
        candidate = path[2]
    else:
        return ""

    if set(query) <= _YOUTUBE_TRACKING and _YOUTUBE_ID.fullmatch(candidate):
        return candidate
    return ""


def source_identity(original_url):
    # Keep the original input on CaptureEvent. Whitespace around a pasted URL does
    # not change its identity, but whitespace or controls in the URL itself do.
    if any(ord(char) < 32 or ord(char) == 127 for char in original_url):
        raise UnsafeCaptureURL
    trimmed = original_url.strip()
    if "\\" in trimmed or any(char.isspace() for char in trimmed):
        raise UnsafeCaptureURL
    try:
        parsed = urlsplit(trimmed)
        host = parsed.hostname
        port = parsed.port
        if (
            parsed.scheme not in ("https", "http")
            or not host
            or parsed.username is not None
            or parsed.netloc.endswith(":")
            or port == 0
        ):
            raise UnsafeCaptureURL
        if parsed.netloc.startswith("[") and not re.fullmatch(
            r"\[[0-9a-fA-F:.]+\](?::[0-9]+)?", parsed.netloc
        ):
            raise UnsafeCaptureURL
        _require_public_hostname(host)
    except (UnicodeError, ValueError):
        raise UnsafeCaptureURL from None

    # Preserve the path, query and fragment byte-for-byte, including delimiters.
    authority_start = trimmed.index("://") + 3
    suffix = trimmed[authority_start + len(parsed.netloc) :]
    platform_id = _youtube_id(parsed, suffix, port)
    if platform_id:
        return SourceIdentity(
            f"https://www.youtube.com/watch?v={platform_id}", "youtube", platform_id
        )

    authority = parsed.netloc.lower() if parsed.netloc.isascii() else parsed.netloc
    return SourceIdentity(f"{parsed.scheme}://{authority}{suffix}")
