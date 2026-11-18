import hashlib
import ipaddress
import unittest
from datetime import UTC, datetime
from unittest.mock import Mock

from .source_fetch import SourceMaterial, SourceStatus, fetch_source
from .source_http import Response

PUBLIC_IP = ipaddress.ip_address("93.184.216.34")
PRIVATE_IP = ipaddress.ip_address("127.0.0.1")
PAGE_URL = "https://example.test/article"


class SourceFetchTests(unittest.TestCase):
    def setUp(self):
        self.resolve = Mock(return_value=(PUBLIC_IP,))
        self.transport = Mock()

    def fetch(self, url=PAGE_URL, **options):
        return fetch_source(url, resolver=self.resolve, transport=self.transport, **options)

    def test_html_metadata_and_web_text_with_provenance(self):
        body = """<!DOCTYPE html><html><head><title>Tiêu đề HTML</title>
<meta property="og:title" content="Tiêu đề &amp; ghi chú">
<meta name="description" content="Đọc bài gốc"></head>
<body><main><h1>Nội dung</h1><p>Tiếng <strong>Việt</strong>.</p>
<script>SECRET()</script><template><p>Hidden</p></template>
<p>Hết.</p></main></body></html>""".encode("utf-8")
        self.transport.return_value = Response(200, media_type="text/html", body=body)

        start = datetime.now(UTC)
        result = self.fetch(PAGE_URL + "#paragraph")
        self.assertEqual(result.status, SourceStatus.FETCHED)
        self.assertEqual(result.metadata.title, "Tiêu đề & ghi chú")
        self.assertEqual(result.metadata.description, "Đọc bài gốc")
        self.assertEqual(result.text, "Nội dung\nTiếng Việt.\nHết.")
        self.assertEqual(result.available, (SourceMaterial.METADATA, SourceMaterial.WEB_TEXT))
        self.assertEqual(result.provenance.source_url, PAGE_URL + "#paragraph")
        self.assertEqual(result.provenance.response_url, PAGE_URL)
        self.assertEqual(result.provenance.http_status, 200)
        self.assertEqual(result.provenance.content_type, "text/html")
        self.assertEqual(result.provenance.body_sha256, hashlib.sha256(body).hexdigest())
        self.assertLessEqual(start, result.provenance.attempted_at)
        self.assertLessEqual(result.provenance.attempted_at, datetime.now(UTC))

    def test_metadata_only_empty_html_and_web_text_are_distinct(self):
        cases = (
            (b"<head><title>Video page</title></head>", "text/html", "fetched", ("metadata",)),
            (b"<script>secret()</script>", "text/html", "empty", ()),
            ("Điện thoại\0".encode("utf-16"), "text/plain", "fetched", ("web_text",)),
            (b"WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nTest", "text/vtt", "unsupported", ()),
            (b"video bytes", "video/mp4", "unsupported", ()),
        )
        for body, media_type, status, materials in cases:
            with self.subTest(media_type=media_type, materials=materials):
                self.transport.return_value = Response(200, media_type=media_type, body=body)
                result = self.fetch()
                self.assertEqual(result.status, status)
                self.assertEqual(result.available, materials)
                self.assertNotIn(SourceMaterial.SUBTITLES, result.available)
                self.assertNotIn(SourceMaterial.VIDEO, result.available)
                if media_type == "text/plain":
                    self.assertEqual(result.text, "Điện thoại")
                else:
                    self.assertIsNone(result.text)

    def test_http_failures_keep_exact_link_timestamp_and_status(self):
        original_url = "https://example.test/private#original"
        cases = (
            (401, SourceStatus.ACCESS_DENIED),
            (403, SourceStatus.ACCESS_DENIED),
            (404, SourceStatus.NOT_FOUND),
            (410, SourceStatus.NOT_FOUND),
            (429, SourceStatus.FAILED),
            (503, SourceStatus.FAILED),
        )
        for status_code, expected in cases:
            with self.subTest(status_code=status_code):
                self.transport.return_value = Response(
                    status_code, media_type="text/html", body=b"<title>Error page</title>"
                )
                result = self.fetch(original_url)
                self.assertEqual(result.status, expected)
                self.assertEqual(result.provenance.source_url, original_url)
                self.assertEqual(result.provenance.response_url, original_url.split("#")[0])
                self.assertEqual(result.provenance.http_status, status_code)
                self.assertIs(result.provenance.attempted_at.tzinfo, UTC)
                self.assertIsNone(result.provenance.body_sha256)
                self.assertEqual(result.available, ())

    def test_blocks_local_nonpublic_and_ambiguous_inputs_before_connect(self):
        urls = (
            "http://localhost./",
            "http://server/",
            "http://host.local/",
            "http://host.home.arpa/",
            "http://127.0.0.1/",
            "http://10.0.0.1/",
            "http://100.64.0.1/",
            "http://169.254.169.254/",
            "http://224.0.0.1/",
            "http://240.0.0.1/",
            "http://[::1]/",
            "http://[fe80::1]/",
            "http://[ff02::1]/",
            "http://[::ffff:127.0.0.1]/",
            "http://[64:ff9b::7f00:1]/",
            "http://[2002:7f00:1::]/",
            "http://[2001:db8::1]/",
            "http://[fe80::1%25eth0]/",
            "http://user:pass@example.test/",
            "http://example.test%2e/",
            "https://[2606:4700::1]suffix/",
            "file:///example",
            "http://example.test/\r\nHost:bad.test",
            "http://example.test\\@127.0.0.1/",
        )
        for url in urls:
            with self.subTest(url=url):
                result = self.fetch(url)
                self.assertEqual(result.status, SourceStatus.BLOCKED)
                self.assertEqual(result.provenance.source_url, url)
        self.transport.assert_not_called()
        self.resolve.assert_not_called()

    def test_rejects_any_nonpublic_dns_answer_before_connect(self):
        self.resolve.return_value = (PUBLIC_IP, PRIVATE_IP)
        for url in (PAGE_URL, "http://127.1/"):
            with self.subTest(url=url):
                result = self.fetch(url)
                self.assertEqual(result.error_code, "blocked_address")
        self.transport.assert_not_called()

    def test_redirect_resolves_same_hostname_again_and_blocks_rebinding(self):
        self.resolve.side_effect = [(PUBLIC_IP,), (PRIVATE_IP,)]
        self.transport.return_value = Response(302, location="/new")

        result = self.fetch()

        self.assertEqual(result.status, SourceStatus.BLOCKED)
        self.assertEqual(result.error_code, "blocked_address")
        self.assertEqual(result.provenance.response_url, PAGE_URL)
        self.assertEqual(result.provenance.http_status, 302)
        self.assertEqual(self.resolve.call_count, 2)
        self.transport.assert_called_once()
        self.assertEqual(self.transport.call_args.args[1], (PUBLIC_IP,))

    def test_redirect_normalizes_url_and_pins_each_public_address(self):
        second_ip = ipaddress.ip_address("2606:4700::1111")
        self.resolve.side_effect = [(PUBLIC_IP,), (second_ip,)]
        self.transport.side_effect = [
            Response(302, location="//other.test/tiếng?lang=vi#hidden"),
            Response(200, media_type="text/plain", body=b"Content"),
        ]

        result = self.fetch()

        self.assertEqual(result.text, "Content")
        self.assertEqual(result.provenance.source_url, PAGE_URL)
        self.assertEqual(result.provenance.response_url, "https://other.test/ti%E1%BA%BFng?lang=vi")
        first, second = (call.args for call in self.transport.call_args_list)
        self.assertEqual(first[1], (PUBLIC_IP,))
        self.assertEqual(second[1], (second_ip,))
        self.assertEqual(first[2], second[2])

    def test_redirect_to_private_ip_or_unsafe_scheme_never_connects(self):
        for location in ("//169.254.169.254/latest", "file:///etc/passwd", "https:/other.test"):
            with self.subTest(location=location):
                self.transport.reset_mock()
                self.transport.return_value = Response(302, location=location)
                result = self.fetch()
                self.assertEqual(result.status, SourceStatus.BLOCKED)
                self.transport.assert_called_once()

    def test_redirect_loop_missing_location_and_hop_limit(self):
        cases = (
            ("/article", 5, "redirect_loop"),
            (None, 5, "redirect_missing_location"),
            ("/different", 0, "redirect_limit"),
        )
        for location, limit, code in cases:
            with self.subTest(code=code):
                self.transport.reset_mock()
                self.transport.return_value = Response(302, location=location)
                result = self.fetch(max_redirects=limit)
                self.assertEqual(result.error_code, code)
                self.transport.assert_called_once()

    def test_body_limit_and_timeout_do_not_yield_content(self):
        self.transport.return_value = Response(200, media_type="text/plain", body=b"abcd")
        result = self.fetch(max_body_bytes=3)
        self.assertEqual(result.error_code, "body_too_large")
        self.assertEqual(result.provenance.http_status, 200)
        self.assertIsNone(result.provenance.body_sha256)
        self.assertEqual(result.available, ())

        self.transport.side_effect = TimeoutError
        result = self.fetch()
        self.assertEqual(result.error_code, "timeout")
        self.assertEqual(result.provenance.source_url, PAGE_URL)
        self.assertIsNone(result.provenance.http_status)
        self.assertEqual(result.available, ())
