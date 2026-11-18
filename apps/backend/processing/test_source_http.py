import ipaddress
import os
import socket
import ssl
import unittest
from time import monotonic
from unittest.mock import Mock, patch

from .source_fetch import SourceStatus, fetch_source
from .source_http import FetchError, parse_target, request_source, resolve_host

PUBLIC_IP = ipaddress.ip_address("93.184.216.34")
PUBLIC_V6 = ipaddress.ip_address("2606:4700::1111")
BASE_URL = "https://example.test/"
TEXT_HEADERS = b"HTTP/1.1 200 OK\r\nContent-Type: text/plain"


class SocketFixture:
    def __init__(self, wire: bytes, *, bytes_per_read=8192, on_read=None):
        self.wire = memoryview(wire)
        self.bytes_per_read = bytes_per_read
        self.on_read = on_read
        self.closed = False
        self.connect = Mock()
        self.sendall = Mock()
        self.settimeout = Mock()

    def recv_into(self, buffer):
        if self.on_read is not None:
            self.on_read()
        size = min(len(buffer), len(self.wire), self.bytes_per_read)
        buffer[:size] = self.wire[:size]
        self.wire = self.wire[size:]
        return size

    def close(self):
        self.closed = True


class SourceTransportTests(unittest.TestCase):
    def request(self, wire, *, limit=32, **options):
        fixture = SocketFixture(wire, **options)
        target = parse_target("http://example.test/")
        with patch("processing.source_http.socket.socket", return_value=fixture):
            response = request_source(target, (PUBLIC_IP,), monotonic() + 5, limit)
        self.assertTrue(fixture.closed)
        return response

    def test_https_connects_to_numeric_ip_and_preserves_hostname_for_tls_and_host(self):
        wire = TEXT_HEADERS + b"; charset=utf-8\r\nContent-Length: 2\r\n\r\nOK"
        fixture = SocketFixture(wire)
        context = Mock()
        context.wrap_socket.return_value = fixture
        with (
            patch("processing.source_http.socket.socket", return_value=fixture) as make_socket,
            patch("processing.source_http.ssl.create_default_context", return_value=context),
            patch("processing.source_http.socket.getaddrinfo") as dns,
            patch.dict(os.environ, {"HTTPS_PROXY": "http://127.0.0.1:8080"}),
        ):
            target = parse_target("https://EXAMPLE.test:8443/tiếng?q=vi#local")
            response = request_source(target, (PUBLIC_V6,), monotonic() + 5, 32)

        self.assertEqual(response.body, b"OK")
        self.assertEqual(response.charset, "utf-8")
        self.assertTrue(fixture.closed)
        make_socket.assert_called_once_with(socket.AF_INET6, socket.SOCK_STREAM)
        fixture.connect.assert_called_once_with(("2606:4700::1111", 8443))
        context.wrap_socket.assert_called_once_with(fixture, server_hostname="example.test")
        dns.assert_not_called()
        request = fixture.sendall.call_args.args[0]
        self.assertTrue(request.startswith(b"GET /ti%E1%BA%BFng?q=vi HTTP/1.1\r\n"))
        self.assertIn(b"\r\nHost: example.test:8443\r\n", request)
        self.assertIn(b"\r\nAccept-Encoding: identity\r\n", request)
        self.assertNotIn(b"#local", request)

    def test_tls_certificate_error_preserves_link_closes_socket_and_never_sends_get(self):
        fixture = SocketFixture(b"")
        context = Mock()
        context.wrap_socket.side_effect = ssl.SSLCertVerificationError(1, "certificate")
        with (
            patch("processing.source_http.socket.socket", return_value=fixture),
            patch("processing.source_http.ssl.create_default_context", return_value=context),
        ):
            result = fetch_source(BASE_URL, resolver=lambda host, deadline: (PUBLIC_IP,))
        self.assertTrue(fixture.closed)
        fixture.sendall.assert_not_called()
        self.assertEqual(result.status, SourceStatus.FAILED)
        self.assertEqual(result.error_code, "tls_certificate_error")
        self.assertEqual(result.provenance.source_url, BASE_URL)

    def test_system_dns_uses_an_absolute_host_and_returns_numeric_ip_objects(self):
        records = [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (str(PUBLIC_IP), 0)),
            (socket.AF_INET6, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (str(PUBLIC_V6), 0, 0, 0)),
        ]
        with patch("processing.source_http.socket.getaddrinfo", return_value=records) as dns:
            self.assertEqual(resolve_host("example.test", monotonic() + 5), (PUBLIC_IP, PUBLIC_V6))
        dns.assert_called_once_with(
            "example.test.", None, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
        )

    def test_connection_falls_back_to_another_already_validated_address(self):
        broken = SocketFixture(b"")
        broken.connect.side_effect = OSError("unreachable")
        working = SocketFixture(TEXT_HEADERS + b"\r\nContent-Length: 2\r\n\r\nOK")
        with patch("processing.source_http.socket.socket", side_effect=[broken, working]):
            result = request_source(
                parse_target("http://example.test/"), (PUBLIC_V6, PUBLIC_IP), monotonic() + 5, 32
            )
        broken.connect.assert_called_once_with(("2606:4700::1111", 80))
        working.connect.assert_called_once_with(("93.184.216.34", 80))
        self.assertEqual(result.body, b"OK")
        self.assertTrue(broken.closed)
        self.assertTrue(working.closed)

    def test_content_length_chunked_and_close_delimited_size_limits(self):
        cases = (
            b"\r\nContent-Length: 4\r\n\r\nabcd",
            b"\r\nTransfer-Encoding: chunked\r\n\r\n4\r\nabcd\r\n0\r\n\r\n",
            b"\r\n\r\nabcd",
        )
        for wire in cases:
            with self.subTest(wire=wire):
                response = self.request(TEXT_HEADERS + wire, limit=3)
                self.assertEqual(response.status, 200)
                self.assertEqual(response.error_code, "body_too_large")
                self.assertIsNone(response.body)
                self.assertEqual(self.request(TEXT_HEADERS + wire, limit=4).body, b"abcd")

    def test_incomplete_and_ambiguous_body_framing_yield_no_body(self):
        for wire, expected in (
            (b"\r\nContent-Length: 3\r\n\r\nab", "incomplete_body"),
            (b"\r\nTransfer-Encoding: chunked\r\n\r\n3\r\nab", "incomplete_body"),
            (
                b"\r\nTransfer-Encoding: chunked\r\nContent-Length: 0\r\n\r\n0\r\n\r\n",
                "invalid_response",
            ),
            (b"\r\nContent-Length: +3\r\n\r\nabc", "invalid_response"),
        ):
            with self.subTest(wire=wire):
                response = self.request(TEXT_HEADERS + wire)
                self.assertEqual(response.error_code, expected)
                self.assertIsNone(response.body)

    def test_compressed_and_nontext_bodies_are_not_consumed(self):
        response = self.request(TEXT_HEADERS + b"\r\nContent-Encoding: gzip\r\n\r\ncompressed")
        self.assertEqual(response.error_code, "unsupported_content_encoding")
        self.assertIsNone(response.body)
        for wire in (
            b"HTTP/1.1 200 OK\r\nContent-Type: video/mp4\r\n\r\nbytes",
            b"HTTP/1.1 200 OK\r\nContent-Type: broken\r\n\r\nbody",
            b"HTTP/1.1 200 OK\r\n\r\nbody",
            b"HTTP/1.1 403 Forbidden\r\nContent-Type: text/html\r\n\r\nprivate",
        ):
            with self.subTest(wire=wire):
                self.assertIsNone(self.request(wire).body)

    def test_absolute_deadline_stops_trickling_headers(self):
        reads = 0

        def advance_clock():
            nonlocal reads
            reads += 1

        fixture = SocketFixture(
            TEXT_HEADERS + b"\r\n\r\nOK", bytes_per_read=1, on_read=advance_clock
        )
        with (
            patch("processing.source_http.socket.socket", return_value=fixture),
            patch("processing.source_http.monotonic", side_effect=lambda: reads / 10),
            self.assertRaises(TimeoutError),
        ):
            request_source(parse_target("http://example.test/"), (PUBLIC_IP,), 0.5, 32)
        self.assertEqual(reads, 5)
        self.assertTrue(fixture.closed)

    def test_wire_budget_limits_interim_headers(self):
        interim = b"HTTP/1.1 100 Continue\r\nX-Fill: " + b"x" * 48_000 + b"\r\n\r\n"
        wire = interim * 3
        with self.assertRaisesRegex(FetchError, "^response_too_large$"):
            self.request(wire)
