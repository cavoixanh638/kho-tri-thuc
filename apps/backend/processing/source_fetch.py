"""Retrieve evidence from public web URLs for a background job."""

import hashlib
import http.client
import math
import ssl
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from html.parser import HTMLParser
from time import monotonic
from urllib.parse import urljoin, urlsplit

from .source_http import (
    HTML_TYPES,
    REDIRECT_STATUSES,
    TEXT_TYPES,
    FetchError,
    Resolver,
    Transport,
    check_url_reference,
    parse_target,
    public_addresses,
    remaining,
    request_source,
    resolve_host,
)


class SourceStatus(StrEnum):
    FETCHED = "fetched"
    EMPTY = "empty"
    NOT_FOUND = "not_found"
    ACCESS_DENIED = "access_denied"
    BLOCKED = "blocked"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


class SourceMaterial(StrEnum):
    METADATA = "metadata"
    WEB_TEXT = "web_text"
    SUBTITLES = "subtitles"
    VIDEO = "video"


@dataclass(frozen=True)
class SourceMetadata:
    title: str = ""
    description: str = ""


@dataclass(frozen=True)
class SourceProvenance:
    source_url: str
    attempted_at: datetime
    response_url: str | None = None
    http_status: int | None = None
    content_type: str | None = None
    body_sha256: str | None = None
    processor: str = "public_web"
    processor_version: str = "public-web-text-v2"


@dataclass(frozen=True)
class SourceResult:
    status: SourceStatus
    provenance: SourceProvenance
    metadata: SourceMetadata | None = None
    text: str | None = None
    error_code: str | None = None

    @property
    def available(self) -> tuple[SourceMaterial, ...]:
        materials = []
        if self.metadata is not None:
            materials.append(SourceMaterial.METADATA)
        if self.text is not None:
            materials.append(SourceMaterial.WEB_TEXT)
        return tuple(materials)


_IGNORED_TAGS = {
    "script",
    "style",
    "template",
    "noscript",
    "svg",
    "iframe",
    "nav",
    "aside",
    "footer",
    "form",
}
_BLOCK_TAGS = {
    "article",
    "aside",
    "blockquote",
    "br",
    "dd",
    "div",
    "dl",
    "dt",
    "figcaption",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "td",
    "tr",
    "ul",
}


class _PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self.primary_parts: list[str] = []
        self.primary_depth = 0
        self.meta: dict[str, str] = {}
        self.in_head = False
        self.in_title = False
        self.ignored_tag: str | None = None
        self.ignored_depth = 0

    def append_text(self, value):
        self.text_parts.append(value)
        if self.primary_depth:
            self.primary_parts.append(value)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.ignored_tag:
            if tag == self.ignored_tag:
                self.ignored_depth += 1
            return
        if tag in _IGNORED_TAGS:
            self.ignored_tag = tag
            self.ignored_depth = 1
        elif tag == "head":
            self.in_head = True
        elif tag == "body":
            self.in_head = False
            self.in_title = False
        elif tag == "title":
            self.in_title = True
        elif tag == "meta":
            attributes = dict(attrs)
            name = (attributes.get("property") or attributes.get("name") or "").lower()
            value = attributes.get("content")
            if name in {"og:title", "og:description", "description"} and value:
                self.meta.setdefault(name, " ".join(value.split())[:2048])
        elif tag in _BLOCK_TAGS:
            if tag in {"main", "article"}:
                self.primary_depth += 1
            self.append_text("\n")

    def handle_endtag(self, tag: str) -> None:
        if self.ignored_tag:
            if tag == self.ignored_tag:
                self.ignored_depth -= 1
                if not self.ignored_depth:
                    self.ignored_tag = None
            return
        if tag == "head":
            self.in_head = False
            self.in_title = False
        elif tag == "title":
            self.in_title = False
        elif tag in _BLOCK_TAGS:
            self.append_text("\n")
            if tag in {"main", "article"}:
                self.primary_depth = max(0, self.primary_depth - 1)

    def handle_data(self, data: str) -> None:
        if self.ignored_tag:
            return
        if self.in_title:
            self.title_parts.append(data)
        elif not self.in_head:
            self.append_text(data)

    def result(self) -> tuple[SourceMetadata | None, str | None]:
        title = self.meta.get("og:title") or " ".join("".join(self.title_parts).split())
        description = self.meta.get("og:description") or self.meta.get(
            "description", ""
        )
        selected = (
            self.primary_parts
            if "".join(self.primary_parts).strip()
            else self.text_parts
        )
        lines = (" ".join(line.split()) for line in "".join(selected).splitlines())
        text = "\n".join(line for line in lines if line)
        metadata = (
            SourceMetadata(title[:512], description) if title or description else None
        )
        return metadata, text or None


def _decode(body: bytes, charset: str | None) -> str:
    if body.startswith((b"\xff\xfe", b"\xfe\xff")):
        charset = "utf-16"
    elif body.startswith(b"\xef\xbb\xbf"):
        charset = "utf-8-sig"
    try:
        text = body.decode(charset or "utf-8", errors="replace")
    except (LookupError, UnicodeError, ValueError):
        text = body.decode("utf-8", errors="replace")
    # PostgreSQL text cannot store NUL, and non-scalar Unicode is not valid UTF-8.
    return text.replace("\0", "").encode("utf-8", errors="replace").decode("utf-8")


def fetch_source(
    url: str,
    *,
    timeout_seconds: float = 10.0,
    max_body_bytes: int = 1024 * 1024,
    max_redirects: int = 5,
    resolver: Resolver = resolve_host,
    transport: Transport = request_source,
) -> SourceResult:
    """Fetch web metadata/body where available; never write models or files.

    The source URL is carried verbatim, including on failure. The timestamp marks
    this attempt. The response fields describe the last observed HTTP response.
    """
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be finite and positive")
    if max_body_bytes <= 0 or max_redirects < 0:
        raise ValueError("invalid body or redirect limit")

    provenance = SourceProvenance(url, datetime.now(UTC))
    deadline = monotonic() + timeout_seconds
    seen = set()
    current_url = url

    def failed(status: SourceStatus, code: str) -> SourceResult:
        return SourceResult(status, provenance, error_code=code)

    try:
        for hop in range(max_redirects + 1):
            remaining(deadline)
            target = parse_target(current_url)
            if target.url in seen:
                return failed(SourceStatus.FAILED, "redirect_loop")
            seen.add(target.url)
            addresses = public_addresses(target.hostname, resolver, deadline)
            remaining(deadline)
            response = transport(target, addresses, deadline, max_body_bytes)
            provenance = replace(
                provenance,
                response_url=target.url,
                http_status=response.status,
                content_type=response.media_type,
            )
            remaining(deadline)

            if response.status not in REDIRECT_STATUSES:
                break
            if not response.location:
                return failed(SourceStatus.FAILED, "redirect_missing_location")
            if hop == max_redirects:
                return failed(SourceStatus.FAILED, "redirect_limit")
            check_url_reference(response.location)
            try:
                if urlsplit(response.location).scheme:
                    current_url = response.location
                else:
                    current_url = urljoin(target.url, response.location)
            except ValueError:
                raise FetchError("invalid_url") from None
    except FetchError as error:
        code = str(error)
        status = (
            SourceStatus.BLOCKED
            if code in {"blocked_address", "invalid_url"}
            else SourceStatus.FAILED
        )
        return failed(status, code)
    except TimeoutError:
        return failed(SourceStatus.FAILED, "timeout")
    except ssl.SSLCertVerificationError:
        return failed(SourceStatus.FAILED, "tls_certificate_error")
    except ssl.SSLError:
        return failed(SourceStatus.FAILED, "tls_error")
    except (http.client.HTTPException, ValueError, OverflowError):
        return failed(SourceStatus.FAILED, "invalid_response")
    except OSError:
        return failed(SourceStatus.FAILED, "network_error")

    if response.status in {404, 410}:
        return failed(SourceStatus.NOT_FOUND, "http_not_found")
    if response.status in {401, 403}:
        return failed(SourceStatus.ACCESS_DENIED, "http_access_denied")
    if response.status != 200:
        return failed(SourceStatus.FAILED, "http_status")
    if response.error_code:
        status = (
            SourceStatus.UNSUPPORTED
            if response.error_code == "unsupported_content_encoding"
            else SourceStatus.FAILED
        )
        return failed(status, response.error_code)
    if response.media_type not in TEXT_TYPES:
        return failed(SourceStatus.UNSUPPORTED, "unsupported_content_type")
    if response.body is None:
        return failed(SourceStatus.FAILED, "incomplete_body")
    if len(response.body) > max_body_bytes:
        return failed(SourceStatus.FAILED, "body_too_large")

    provenance = replace(
        provenance, body_sha256=hashlib.sha256(response.body).hexdigest()
    )
    decoded = _decode(response.body, response.charset)
    if response.media_type in HTML_TYPES:
        parser = _PageParser()
        try:
            parser.feed(decoded)
            parser.close()
        except (AssertionError, ValueError):
            return failed(SourceStatus.FAILED, "invalid_html")
        metadata, text = parser.result()
    else:
        metadata, text = None, decoded.strip() or None
    if monotonic() >= deadline:
        return failed(SourceStatus.FAILED, "timeout")
    if metadata is None and text is None:
        return failed(SourceStatus.EMPTY, "no_content")
    return SourceResult(SourceStatus.FETCHED, provenance, metadata=metadata, text=text)
