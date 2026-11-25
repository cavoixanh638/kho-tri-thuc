"""P05 isolated clipper regression suite; no external network or private data."""

import hashlib
from types import SimpleNamespace
from unittest.mock import patch

from catalog.models import Item, Source
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from ingestion.models import CaptureEvent
from processing.clips import anchor, digest, safe_url
from processing.models import ClipAnnotation, DerivedContent


def fetched(text, *, status="fetched", http_status=200):
    return SimpleNamespace(
        text=text if status == "fetched" else None,
        status=status,
        metadata=SimpleNamespace(title="Public fixture") if status == "fetched" else None,
        provenance=SimpleNamespace(
            processor="public_web", processor_version="fixture-v2",
            body_sha256=digest(text), http_status=http_status,
        ),
    )


class P05ClipRegression(TransactionTestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="p05-owner")
        self.other = get_user_model().objects.create_user(username="p05-other")
        self.client.force_login(self.owner)
        self.item = Item.objects.create(owner=self.owner, kind="text", note="Gốc\r\n  giữ nguyên  ")

    def post(self, path, data, key=None):
        headers = {"Idempotency-Key": key} if key else {}
        return self.client.post(
            "/api/v1" + path, data, content_type="application/json", headers=headers
        )

    def preview(self, *, url="https://example.org/source", mode="selection", quote="đúng"):
        return self.post("/clips/preview", {
            "mode": mode, "url": url, "quote": quote,
            "target_item_id": str(self.item.pk),
        })

    def test_thirty_exact_unicode_offsets_and_ambiguous_quotes(self):
        # 30 ground-truth fixtures: combining accents, emoji and repeated excerpts.
        for i in range(30):
            quote = f"📌 №{i:02d} Tiếng Việt ế — đoạn cần giữ"
            before = ("前🙂" * (i % 7)) + "\n"
            text = before + quote + "\n" + ("尾" * (i % 5))
            start = len(before)
            self.assertEqual(
                anchor(text, quote, start, start + len(quote)),
                {"text_start": start, "text_end": start + len(quote),
                 "offset_unit": "unicode_codepoint"},
            )
            self.assertEqual(digest(text), hashlib.sha256(text.encode()).hexdigest())
            self.assertIsNone(anchor(text, quote, start + 1, start + len(quote) + 1))
            self.assertIsNone(anchor(text, quote, True, start + len(quote)))
            self.assertIsNone(anchor(text, quote, start, False))
            self.assertIsNone(anchor(text + quote, quote))
            self.assertIsNotNone(anchor(text + quote, quote, start, start + len(quote)))

    def test_canonical_source_binding_note_unchanged_and_conflicting_retry(self):
        first = "https://EXAMPLE.org/article"
        second = "https://example.org/article"
        with patch("processing.clips.fetch_source", return_value=fetched("Đầu đúng cuối")):
            a = self.preview(url=first)
            self.assertEqual(a.status_code, 200, a.content)
            self.assertEqual(a.json()["fetch_status"], "fetched")
            saved = self.post("/clips", {"receipt": a.json()["receipt"]}, "p05-key")
            self.assertEqual(saved.status_code, 201, saved.content)
            self.assertEqual(
                self.post("/clips", {"receipt": a.json()["receipt"]}, "p05-key").status_code,
                200,
            )
            b = self.preview(url=second, quote="Đầu")
            self.assertEqual(b.status_code, 200)
            conflict = self.post("/clips", {"receipt": b.json()["receipt"]}, "p05-key")
            self.assertEqual(conflict.status_code, 409, conflict.content)
            self.assertEqual(conflict.json()["code"], "clip_idempotency_receipt_conflict")
            saved2 = self.post("/clips", {"receipt": b.json()["receipt"]}, "p05-new-key")
            self.assertEqual(saved2.status_code, 201, saved2.content)
        self.assertEqual(CaptureEvent.objects.filter(item=self.item).count(), 2)
        self.assertEqual(ClipAnnotation.objects.filter(item=self.item).count(), 2)
        self.assertEqual(Source.objects.filter(item=self.item).count(), 1)
        for row in ClipAnnotation.objects.filter(item=self.item):
            self.assertIsNotNone(row.source_id)
            self.assertIsNotNone(row.part_id)
            self.assertEqual(row.part.source_locator["source_id"], row.source_id)
        self.assertEqual(Item.objects.get(pk=self.item.pk).note, "Gốc\r\n  giữ nguyên  ")

    def test_source_versions_stale_and_owner_ownership(self):
        with patch("processing.clips.fetch_source", return_value=fetched("x đúng y")):
            pre = self.preview()
        saved = self.post("/clips", {"receipt": pre.json()["receipt"]}, "p05-version")
        self.assertEqual(saved.status_code, 201)
        annotation = ClipAnnotation.objects.get(pk=saved.json()["annotation_id"])
        self.assertEqual(
            self.client.get(f"/api/v1/clips/{annotation.pk}/source").status_code, 200
        )
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(f"/api/v1/clips/{annotation.pk}/source").status_code, 404)
        self.assertEqual(self.post("/clips", {"receipt": pre.json()["receipt"]}, "other").status_code, 404)
        self.client.force_login(self.owner)
        annotation.part.processor_version = "changed"
        annotation.part.save(update_fields=["processor_version"])
        stale = self.client.get(f"/api/v1/clips/{annotation.pk}/source")
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(stale.json()["state"], "stale")
        self.assertEqual(Item.objects.get(pk=self.item.pk).note, "Gốc\r\n  giữ nguyên  ")

    def test_403_429_bad_charset_long_article_and_unverified_quote(self):
        for status, http_status in (("access_denied", 403), ("failed", 429),
                                    ("blocked", None)):
            with self.subTest(status=status):
                with patch("processing.clips.fetch_source", return_value=fetched("", status=status, http_status=http_status)):
                    response = self.preview()
                self.assertEqual(response.status_code, 200, response.content)
                self.assertEqual(response.json()["verification"], "unverified")
                self.assertEqual(response.json()["fetch_status"], status)
                self.assertEqual(response.json()["http_status"], http_status)
                self.assertEqual(CaptureEvent.objects.count(), 0)
        with patch("processing.clips.fetch_source", return_value=fetched("bad � charset")):
            result = self.preview(quote="not in source")
        self.assertEqual(result.json()["verification"], "unverified")
        with patch("processing.clips.fetch_source", return_value=fetched("A" * 75000)):
            result = self.preview(mode="article", quote="")
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json()["truncated"])
        self.assertEqual(len(result.json()["quote"]), 60000)

    def test_invalid_inputs_fail_before_any_network_and_ssrf_is_blocked(self):
        with patch("processing.clips.fetch_source") as fetch:
            for quote in ("x" * 60001, "hi\0", "\ud800", ""):
                with self.subTest(quote=repr(quote)[:30]):
                    response = self.preview(quote=quote)
                    self.assertEqual(response.status_code, 422, response.content)
            fetch.assert_not_called()
        for url in (
            "http://127.0.0.1/private", "http://169.254.169.254/latest",
            "https://localhost/", "https://user:password@example.org/",
            "https://example.org/?access_token=private",
            "https://example.org/#api_key=private",
            "javascript:alert(1)",
        ):
            with self.subTest(url=url):
                try:
                    safe_url(url)
                except ValueError:
                    pass
                else:
                    self.fail(f"Unsafe URL accepted: {url}")
        self.assertEqual(CaptureEvent.objects.count(), 0)

    def test_repeated_source_quote_requires_explicit_matching_offsets(self):
        text = "đúng — sai — đúng"
        with patch("processing.clips.fetch_source", return_value=fetched(text)):
            ambiguous = self.preview()
        self.assertEqual(ambiguous.status_code, 200)
        self.assertEqual(ambiguous.json()["verification"], "unverified")
        # A quoted phrase from a different source must not be marked verified.
        with patch("processing.clips.fetch_source", return_value=fetched("khác")):
            missing = self.preview()
        self.assertEqual(missing.json()["verification"], "unverified")
