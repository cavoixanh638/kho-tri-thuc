"""P14 encoded credential-key regression for portable Markdown vault sources.

No network, production data, OAuth, external fixture or database write.
"""
from django.test import SimpleTestCase

from .vault import VaultError, _safe_url


class VaultSourceUrlSecurityTests(SimpleTestCase):
    def test_secret_parameter_aliases_and_encoding_are_rejected(self):
        hostile_urls = [
            "https://safe.example/?token=synthetic",
            "https://safe.example/?sig=synthetic",
            "https://safe.example/?TOK%45N=synthetic",
            "https://safe.example/?%74%6F%6B%65%6E=synthetic",
            "https://safe.example/?%2574oken=synthetic",
            "https://safe.example/?X-Amz-Credential=synthetic",
            "https://safe.example/?access_token=synthetic",
            "https://safe.example/#oauth_code=synthetic",
            "https://safe.example/#section?%73ig=synthetic",
            "https://safe.example/?my_refresh_token=synthetic",
            "https://safe.example/?Authorization=synthetic",
            "https://safe.example/?api-key=synthetic",
            "https://safe.example/?jwt=synthetic",
            "https://safe.example/?code=synthetic",
            "https://safe.example/?pw%64=synthetic",
            "https://user:pass@safe.example/document",
        ]
        for url in hostile_urls:
            with self.subTest(url=url), self.assertRaisesRegex(
                VaultError, "unsafe_source_reference"
            ):
                _safe_url(url)

    def test_article_urls_with_benign_queries_remain_portable(self):
        for url in (
            "https://safe.example/reference?title=tokenization",
            "https://safe.example/video?chapter=1&time=02%3A14",
            "https://safe.example/note#heading-2",
            "http://safe.example/view?category=research&topic=signatures",
        ):
            with self.subTest(url=url):
                self.assertIsNone(_safe_url(url))

    def test_missing_or_non_http_urls_rejected(self):
        for url in ("javascript:alert(1)", "file:///etc/passwd", "//safe.example/x"):
            with self.subTest(url=url), self.assertRaisesRegex(
                VaultError, "unsafe_source_reference"
            ):
                _safe_url(url)
        self.assertIsNone(_safe_url("", optional=True))
