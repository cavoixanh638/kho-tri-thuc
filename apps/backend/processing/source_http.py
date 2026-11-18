"""Bounded HTTP GETs over DNS-validated, directly connected sockets."""

import http.client
import io
import ipaddress
import re
import socket
import ssl
from dataclasses import dataclass
from queue import Empty, SimpleQueue
from threading import BoundedSemaphore, Thread
from time import monotonic
from typing import Callable
from urllib.parse import quote, urlsplit, urlunsplit

IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address
Resolver = Callable[[str, float], tuple[IPAddress, ...]]

REDIRECT_STATUSES = {301, 302, 303, 307, 308}
HTML_TYPES = {"text/html", "application/xhtml+xml"}
TEXT_TYPES = HTML_TYPES | {"text/plain"}
_MAX_URL_LENGTH = 8192
_MAX_HTTP_OVERHEAD = 128 * 1024
_DNS_SLOTS = BoundedSemaphore(4)
_GLOBAL_V6 = ipaddress.ip_network("2000::/3")
_LOCAL_SUFFIXES = (".localhost", ".local", ".internal", ".home.arpa")
_AUTHORITY = re.compile(r"(?:\[[^\]]+\]|[^:\[\]]+)(?::[0-9]+)?")
_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")


class FetchError(Exception):
    """A retrieval error with a stable, URL-free code."""


@dataclass(frozen=True)
class Target:
    url: str
    hostname: str
    host_header: str
    port: int
    https: bool
    request_target: str


@dataclass(frozen=True)
class Response:
    status: int
    location: str | None = None
    media_type: str | None = None
    charset: str | None = None
    body: bytes | None = None
    error_code: str | None = None


Transport = Callable[[Target, tuple[IPAddress, ...], float, int], Response]


def check_url_reference(url: str) -> None:
    if (
        not url
        or len(url) > _MAX_URL_LENGTH
        or "\\" in url
        or any(ch.isspace() or ord(ch) < 32 or ord(ch) == 127 for ch in url)
    ):
        raise FetchError("invalid_url")


def parse_target(url: str) -> Target:
    check_url_reference(url)
    try:
        parts = urlsplit(url)
        if parts.scheme not in {"http", "https"} or not _AUTHORITY.fullmatch(parts.netloc):
            raise FetchError("invalid_url")
        if "@" in parts.netloc or "%" in parts.netloc or parts.port == 0:
            raise FetchError("invalid_url")

        https = parts.scheme == "https"
        default_port = 443 if https else 80
        port = parts.port or default_port
        hostname = parts.hostname or ""
        if parts.netloc.startswith("["):
            hostname = str(ipaddress.IPv6Address(hostname))
            host_header = f"[{hostname}]"
        else:
            hostname = hostname.encode("idna").decode("ascii").lower().removesuffix(".")
            if len(hostname) > 253 or not all(
                _LABEL.fullmatch(label) for label in hostname.split(".")
            ):
                raise FetchError("invalid_url")
            host_header = hostname

        if port != default_port:
            host_header = f"{host_header}:{port}"
        path = quote(parts.path or "/", safe="/%:@!$&'()*+,;=-._~")
        query = quote(parts.query, safe="/?%:@!$&'()*+,;=-._~")
        request_target = f"{path}?{query}" if query else path
        normalized_url = urlunsplit((parts.scheme, host_header, path, query, ""))
        return Target(normalized_url, hostname, host_header, port, https, request_target)
    except (UnicodeError, ValueError):
        raise FetchError("invalid_url") from None


def remaining(deadline: float) -> float:
    seconds = deadline - monotonic()
    if seconds <= 0:
        raise TimeoutError
    return seconds


def resolve_host(hostname: str, deadline: float) -> tuple[IPAddress, ...]:
    # System DNS has no per-call timeout. A bounded set of daemon threads lets
    # the caller stop waiting on time without accumulating stuck lookups.
    if not _DNS_SLOTS.acquire(timeout=remaining(deadline)):
        raise TimeoutError
    results: SimpleQueue[tuple[IPAddress, ...] | None] = SimpleQueue()

    def lookup() -> None:
        try:
            records = socket.getaddrinfo(
                f"{hostname}.", None, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
            )
            results.put(tuple(ipaddress.ip_address(record[4][0]) for record in records))
        except (OSError, ValueError):
            results.put(None)
        finally:
            _DNS_SLOTS.release()

    try:
        Thread(target=lookup, daemon=True).start()
    except RuntimeError:
        _DNS_SLOTS.release()
        raise FetchError("dns_error") from None
    try:
        addresses = results.get(timeout=remaining(deadline))
    except Empty:
        raise TimeoutError from None
    if not addresses:
        raise FetchError("dns_error")
    return addresses


def public_addresses(
    hostname: str, resolver: Resolver, deadline: float
) -> tuple[IPAddress, ...]:
    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        if "." not in hostname or hostname.endswith(_LOCAL_SUFFIXES):
            raise FetchError("blocked_address") from None
        addresses = tuple(dict.fromkeys(resolver(hostname, deadline)))
    else:
        addresses = (literal,)

    if not addresses:
        raise FetchError("dns_error")
    for address in addresses:
        if (
            not address.is_global
            or address.is_multicast
            or address.is_reserved
            or (
                address.version == 6
                and (address not in _GLOBAL_V6 or address.sixtofour is not None)
            )
        ):
            raise FetchError("blocked_address")
    return addresses


class _DeadlineReader(io.RawIOBase):
    def __init__(self, connection: socket.socket, deadline: float, allowance: int):
        super().__init__()
        self.connection = connection
        self.deadline = deadline
        self.allowance = allowance

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: bytearray) -> int:
        self.connection.settimeout(remaining(self.deadline))
        # Read at most one extra byte to distinguish a full budget from EOF.
        size = self.connection.recv_into(memoryview(buffer)[: self.allowance + 1])
        self.allowance -= size
        if self.allowance < 0:
            raise FetchError("response_too_large")
        return size


class _ResponseSocket:
    """Provide the buffered read interface used by http.client.HTTPResponse."""

    def __init__(self, reader: _DeadlineReader):
        self.reader = reader

    def makefile(self, mode: str) -> io.BufferedReader:
        return io.BufferedReader(self.reader)


def _connect(
    addresses: tuple[IPAddress, ...], port: int, deadline: float
) -> socket.socket:
    last_error = OSError("no addresses")
    for index, address in enumerate(addresses):
        timeout = remaining(deadline)
        if index < len(addresses) - 1:
            timeout = min(timeout, 2.0)
        family = socket.AF_INET6 if address.version == 6 else socket.AF_INET
        connection = socket.socket(family, socket.SOCK_STREAM)
        try:
            connection.settimeout(timeout)
            # The address is an ipaddress value. No hostname or proxy reaches connect().
            connection.connect((str(address), port))
            return connection
        except OSError as error:
            connection.close()
            last_error = error
    raise last_error


def _read_body(response: http.client.HTTPResponse, limit: int) -> bytes:
    encodings = response.headers.get_all("Content-Encoding", [])
    if encodings and [value.strip().lower() for value in encodings] != ["identity"]:
        raise FetchError("unsupported_content_encoding")

    transfers = response.headers.get_all("Transfer-Encoding", [])
    lengths = response.headers.get_all("Content-Length", [])
    if transfers and (
        lengths or [value.strip().lower() for value in transfers] != ["chunked"]
    ):
        raise FetchError("invalid_response")
    if lengths:
        length = lengths[0].strip()
        if len(lengths) != 1 or not re.fullmatch(r"[0-9]+", length):
            raise FetchError("invalid_response")
        digits = length.lstrip("0") or "0"
        if len(digits) > len(str(limit)) or int(digits) > limit:
            raise FetchError("body_too_large")
        if response.length is None:
            raise FetchError("invalid_response")

    body = response.read(limit + 1)
    if len(body) > limit:
        raise FetchError("body_too_large")
    if response.length:
        raise FetchError("incomplete_body")
    return body


def request_source(
    target: Target, addresses: tuple[IPAddress, ...], deadline: float, max_body_bytes: int
) -> Response:
    connection = _connect(addresses, target.port, deadline)
    try:
        if target.https:
            context = ssl.create_default_context()
            connection.settimeout(remaining(deadline))
            connection = context.wrap_socket(connection, server_hostname=target.hostname)

        request = (
            f"GET {target.request_target} HTTP/1.1\r\n"
            f"Host: {target.host_header}\r\n"
            "User-Agent: KhoTriThuc/1.0\r\n"
            "Accept: text/html, application/xhtml+xml, text/plain\r\n"
            "Accept-Encoding: identity\r\n"
            "Connection: close\r\n\r\n"
        )
        connection.settimeout(remaining(deadline))
        connection.sendall(request.encode("ascii"))
        reader = _DeadlineReader(connection, deadline, max_body_bytes + _MAX_HTTP_OVERHEAD)
        with http.client.HTTPResponse(_ResponseSocket(reader), method="GET") as response:
            response.begin()
            status = response.status
            locations = response.headers.get_all("Location", [])
            location = locations[0] if len(locations) == 1 else None
            content_types = response.headers.get_all("Content-Type", [])
            media_type = None
            charset = None
            if len(content_types) == 1:
                media_type = content_types[0].partition(";")[0].strip().lower()
                charset = response.headers.get_content_charset()
            if status != 200 or media_type not in TEXT_TYPES:
                return Response(status, location, media_type, charset)

            try:
                body = _read_body(response, max_body_bytes)
            except FetchError as error:
                return Response(status, location, media_type, charset, error_code=str(error))
            except TimeoutError:
                return Response(status, location, media_type, charset, error_code="timeout")
            except (http.client.IncompleteRead, ConnectionError):
                return Response(
                    status, location, media_type, charset, error_code="incomplete_body"
                )
            except (http.client.HTTPException, OSError, ValueError, OverflowError):
                return Response(status, location, media_type, charset, error_code="invalid_response")
            return Response(status, location, media_type, charset, body)
    finally:
        connection.close()
