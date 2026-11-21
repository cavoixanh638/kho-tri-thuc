#!/usr/bin/env python3
"""P14 isolated abuse-case regression tests (standard library only).

Run in a checkout of the frozen branch:
    python tools/security/p14_audit.py -v

Optional review of read-only PR62 WIP source:
    python tools/security/p14_audit.py --wip-vault /tmp/p14-vault.py -v

The optional file must be the actual PR62 apps/backend/catalog/vault.py
(fetched independently, NOT merged). No network, DB, Drive, media or live
deployment access is performed by this script. PASS is limited to functions
isolated from their source or static security-contract assertions.
"""
import argparse
import ast
import io
import ipaddress
import re
import stat
import sys
import unicodedata
import unittest
import zipfile
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "apps" / "backend"
sys.path.insert(0, str(BACKEND))


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def isolated(path, function, namespace):
    """Execute ONLY the named source function; never initialize Django/Drive."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"), filename=str(path))
    node = next((x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == function), None)
    if node is None:
        raise AssertionError(f"Missing {function}: {path}")
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), namespace)
    return namespace[function]


class VaultError(ValueError):
    pass


class SecurityAbuseTests(unittest.TestCase):
    wip_vault = None

    @classmethod
    def setUpClass(cls):
        # These modules are stdlib-only and do not initialize Django or networks.
        from processing import source_fetch, source_http
        cls.http, cls.fetch = source_http, source_fetch
        cls.byte_range = staticmethod(isolated(
            BACKEND / "storage" / "viewer_api.py", "selected_range",
            {"re": re, "MAX_RANGE": 4 * 1024 * 1024}))
        if cls.wip_vault:
            ns = {
                "re": re, "stat": stat, "urlsplit": urlsplit, "unquote": unquote,
                "VaultError": VaultError, "io": io, "zipfile": zipfile,
                "unicodedata": unicodedata, "MAX_ARCHIVE": 32 * 1024 * 1024,
                "MAX_EXPANDED": 64 * 1024 * 1024, "MAX_FILE": 2 * 1024 * 1024,
            }
            cls.check_url = staticmethod(isolated(cls.wip_vault, "check_url", ns))
            cls.safe_path = staticmethod(isolated(cls.wip_vault, "safe_path", ns))
            cls.parse_vault = staticmethod(isolated(cls.wip_vault, "parse_vault", ns))
            cls.vault_ns = ns

    def vault_required(self):
        if not self.wip_vault:
            self.skipTest("NOT_RUN: supply read-only PR62 vault.py using --wip-vault")

    def test_01_session_login_csrf_contract(self):
        src = read("apps/backend/config/test_session.py")
        self.assertIn("enforce_csrf_checks=True", src)
        self.assertIn("self.assertEqual(", src)
        self.assertIn("403", src)

    def test_02_session_logout_csrf_contract(self):
        src = read("apps/backend/config/session.py")
        self.assertIn("@require_http_methods", src)
        self.assertIn('elif request.method == "DELETE":', src)
        self.assertIn("logout(request)", src)
        self.assertIn("django.middleware.csrf.CsrfViewMiddleware", read("apps/backend/config/settings.py"))

    def test_03_anonymous_api_all_routes_live(self):
        self.skipTest("NOT_RUN: Django TestClient + temporary PostgreSQL required")

    def test_04_six_sensitive_router_auth_contracts(self):
        files = ("catalog/api.py", "catalog/collection_api.py", "catalog/groups_api.py",
                 "ingestion/api.py", "processing/clip_api.py", "storage/viewer_api.py")
        for file in files:
            with self.subTest(file=file):
                s = (BACKEND / file).read_text(encoding="utf-8")
                self.assertRegex(s, r"Router\([^\n]*auth=django_auth")

    def test_05_item_idor_read(self):
        s = read("apps/backend/catalog/api.py")
        self.assertIn("Item.objects.filter(owner=owner)", s)
        self.assertIn("get_object_or_404(catalog(request.user), pk=item_id)", s)

    def test_06_item_idor_update(self):
        self.assertIn("Item.objects.select_for_update(), pk=item_id, owner=request.user",
                      read("apps/backend/catalog/api.py"))

    def test_07_capture_idor(self):
        s = read("apps/backend/ingestion/api.py")
        self.assertIn("CaptureEvent.objects.filter(owner=request.auth)", s)
        self.assertIn("pk=item_id, owner=request.auth", s)

    def test_08_derived_clip_idor(self):
        s = read("apps/backend/processing/clips.py")
        self.assertIn("item__owner=owner", s)
        self.assertIn("part.asset.item_id != part.item_id", s)

    def test_09_collection_idor(self):
        s = read("apps/backend/catalog/collection_api.py")
        self.assertIn("SavedCollection.objects.filter(owner=request.user)", s)
        self.assertIn("pk=collection_id, owner=request.user", s)

    def test_10_oauth_owner_state_expiry(self):
        s = read("apps/backend/storage/oauth.py")
        self.assertIn('pending["owner"] != str(request.user.pk)', s)
        self.assertIn("secrets.compare_digest", s)
        self.assertIn('time.time() >= pending["expires_at"]', s)

    def test_11_clipper_signed_receipt_expiry(self):
        s = read("apps/backend/processing/clips.py")
        self.assertIn("signing.loads(receipt, salt=SALT, max_age=300)", s)
        self.assertIn('data.get("owner_id") != owner.pk', s)

    def test_12_ssrf_block_non_http_schemes(self):
        for url in ("file:///etc/passwd", "gopher://public.example/x", "ftp://public.example/x"):
            with self.subTest(url=url), self.assertRaises(self.http.FetchError):
                self.http.parse_target(url)

    def test_13_ssrf_userinfo_rejected(self):
        with self.assertRaises(self.http.FetchError):
            self.http.parse_target("http://user:pass@public.example/")

    def test_14_ssrf_private_ipv4(self):
        for addr in ("127.0.0.1", "10.0.0.10", "169.254.169.254", "192.168.1.1"):
            with self.subTest(addr=addr), self.assertRaises(self.http.FetchError):
                self.http.public_addresses(addr, lambda *_: (), 1e99)

    def test_15_ssrf_local_ipv6(self):
        for addr in ("::1", "fd00::1", "::ffff:127.0.0.1"):
            with self.subTest(addr=addr), self.assertRaises(self.http.FetchError):
                self.http.public_addresses(addr, lambda *_: (), 1e99)

    def test_16_ssrf_mixed_dns_public_private(self):
        resolver = lambda *_: (ipaddress.ip_address("8.8.8.8"), ipaddress.ip_address("127.0.0.1"))
        with self.assertRaises(self.http.FetchError):
            self.http.public_addresses("safe.example", resolver, 1e99)

    def test_17_ssrf_redirect_to_private_address(self):
        called = []
        def transport(target, *_):
            called.append(target.hostname)
            return self.http.Response(302, location="http://127.0.0.1/admin")
        result = self.fetch.fetch_source(
            "https://safe.example/", transport=transport,
            resolver=lambda *_: (ipaddress.ip_address("8.8.8.8"),))
        self.assertEqual(result.error_code, "blocked_address")
        self.assertEqual(called, ["safe.example"])

    def test_18_ssrf_redirect_count_limit(self):
        calls = [0]
        def transport(*_):
            calls[0] += 1
            return self.http.Response(302, location=f"/redirect-{calls[0]}")
        result = self.fetch.fetch_source(
            "https://safe.example/", transport=transport, max_redirects=1,
            resolver=lambda *_: (ipaddress.ip_address("8.8.8.8"),))
        self.assertEqual((result.error_code, calls[0]), ("redirect_limit", 2))

    def test_19_ssrf_direct_socket_and_tls_hostname(self):
        s = read("apps/backend/processing/source_http.py")
        self.assertIn("connection.connect((str(address), port))", s)
        self.assertIn("context.wrap_socket(connection, server_hostname=target.hostname)", s)

    def test_20_ssrf_response_limit(self):
        s = read("apps/backend/processing/source_http.py")
        self.assertIn("response.read(limit + 1)", s)
        self.assertIn('raise FetchError("body_too_large")', s)
        self.assertIn("Accept-Encoding: identity", s)

    def test_21_html_script_ignored_during_extraction(self):
        body = b"<html><script>DO_NOT_INCLUDE</script><article>Visible text</article></html>"
        def transport(*_):
            return self.http.Response(200, media_type="text/html", charset="utf-8", body=body)
        result = self.fetch.fetch_source(
            "https://safe.example/", transport=transport,
            resolver=lambda *_: (ipaddress.ip_address("8.8.8.8"),))
        self.assertIn("Visible text", result.text)
        self.assertNotIn("DO_NOT_INCLUDE", result.text)

    def test_22_viewer_owner_authorization(self):
        s = read("apps/backend/storage/viewer_api.py")
        self.assertIn("Router(auth=django_auth", s)
        self.assertIn("item__owner=request.user", s)
        self.assertIn("item__deleted_at__isnull=True", s)

    def test_23_range_multi_range_and_invalid(self):
        for header in ("bytes=0-1,3-4", "bytes=bogus-3", "bytes=-0", "bytes=100-99"):
            with self.subTest(header=header), self.assertRaises(ValueError):
                self.byte_range(header, 100)

    def test_24_range_bounded_large_and_suffix(self):
        upper = 4 * 1024 * 1024
        self.assertEqual(self.byte_range("bytes=0-999999999", 100_000_000), (0, upper - 1, True))
        self.assertEqual(self.byte_range("bytes=-5", 100), (95, 99, True))
        with self.assertRaises(ValueError):
            self.byte_range(None, upper + 1)

    def test_25_viewer_version_etag_and_private_cache(self):
        s = read("apps/backend/storage/viewer_api.py")
        for token in ('sha256 != asset.sha256', 'request.headers.get("If-Range")',
                      '"private, no-store"', '"nosniff"', '"no-referrer"'):
            self.assertIn(token, s)

    def test_26_markdown_xss_and_external_urls(self):
        s = read("apps/web/src/KnowledgeText.tsx")
        api = read("apps/web/src/api.ts")
        self.assertIn("<Markdown skipHtml", s)
        self.assertIn("externalHttpUrl(url)", s)
        self.assertIn('rel="noopener noreferrer"', s)
        self.assertIn("url.protocol === 'https:' || url.protocol === 'http:'", api)

    def test_27_vault_zip_traversal(self):
        self.vault_required()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("../outside.md", "synthetic")
        with self.assertRaises(VaultError):
            self.parse_vault(buf.getvalue(), object())

    def test_28_vault_zip_expansion_limit(self):
        self.vault_required()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("large.md", "X" * 4096)
        previous = self.vault_ns["MAX_EXPANDED"]
        try:
            self.vault_ns["MAX_EXPANDED"] = 1024
            with self.assertRaises(VaultError):
                self.parse_vault(buf.getvalue(), object())
        finally:
            self.vault_ns["MAX_EXPANDED"] = previous

    def test_29_vault_unrecognized_secret_url_aliases(self):
        self.vault_required()
        # WIP PR62 currently FAILS these exact read-only source checks.
        for key in ("token", "sig"):
            with self.subTest(key=key), self.assertRaises(VaultError):
                self.check_url(f"https://safe.example/doc?{key}=synthetic-placeholder")

    def test_30_vault_import_respects_selected_item_scope(self):
        self.vault_required()
        s = self.wip_vault.read_text(encoding="utf-8")
        begin = s.index('for source in data["collections"]:', s.index("def apply_import"))
        end = s.index('for row in data["items"]:', begin)
        block = s[begin:end]
        # WIP PR62 currently FAILS: global collection creation has no selected guard.
        self.assertIn('if source["item_id"] not in selected:', block)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wip-vault", type=Path,
                        help="Exact read-only PR62 catalog/vault.py; never merged into frozen")
    args, rest = parser.parse_known_args()
    if args.wip_vault and not args.wip_vault.is_file():
        parser.error("WIP vault source not found")
    SecurityAbuseTests.wip_vault = args.wip_vault
    unittest.main(argv=[sys.argv[0], *rest], verbosity=2)
