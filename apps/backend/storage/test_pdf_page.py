"""Exact PDF-page provenance: two different colored pages, auth and hash checks."""
from __future__ import annotations

import hashlib
import io
from unittest.mock import patch

from PIL import Image
from catalog.models import Item
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject

from .models import Asset, StorageLocation
from .pdf_page_render import render_page


def colored_pdf():
    document = PdfWriter()
    for rgb in (b"1 0 0 rg", b"0 0 1 rg"):
        page = document.add_blank_page(width=200, height=180)
        stream = DecodedStreamObject()
        stream.set_data(rgb + b"\n0 0 200 180 re f\n")
        page[NameObject("/Contents")] = document._add_object(stream)
    output = io.BytesIO()
    document.write(output)
    return output.getvalue()


def center_pixel(body):
    with Image.open(io.BytesIO(body)) as image:
        with image.convert("RGB") as bitmap:
            return bitmap.getpixel((bitmap.width // 2, bitmap.height // 2))


class ExactPdfPageTests(TestCase):
    def setUp(self):
        user = get_user_model()
        self.owner = user.objects.create_user(username="pdf-page-owner")
        self.other = user.objects.create_user(username="pdf-page-other")
        self.item = Item.objects.create(owner=self.owner, kind="file", note="Nguyên văn riêng\n")
        self.body = colored_pdf()
        self.sha = hashlib.sha256(self.body).hexdigest()
        self.asset = Asset.objects.create(
            item=self.item, mime="application/pdf", size=len(self.body),
            sha256=self.sha, original_filename="synthetic-two-pages.pdf",
            content_version=4,
        )
        StorageLocation.objects.create(
            asset=self.asset, provider_file_id="not-a-real-drive-id",
            provider_revision="fixture", provider="google_drive",
            verified_at=timezone.now(), status="verified",
        )
        self.client.force_login(self.owner)
        self.base = "/api/v1/assets/" + str(self.asset.pk)
        self.url = self.base + "/pdf-page/4/" + self.sha + "/"
        self.factory = patch("storage.viewer_api.storage_for_owner")
        self.port = self.factory.start().return_value
        self.addCleanup(self.factory.stop)
        self.port.read_range.side_effect = (
            lambda asset, start, end: self.body[start:end + 1]
        )

    def test_render_pdf_page_deterministically_renders_correct_1_based_page(self):
        first = render_page(self.body, 1)
        second = render_page(self.body, 2)
        self.assertNotEqual(first, second)
        red = center_pixel(first)
        blue = center_pixel(second)
        self.assertGreater(red[0], 200)
        self.assertLess(red[2], 40)
        self.assertGreater(blue[2], 200)
        self.assertLess(blue[0], 40)

    def test_actual_private_http_endpoint_returns_exact_pdf_page(self):
        descriptor = self.client.get(self.base + "/viewer")
        self.assertEqual(descriptor.status_code, 200)
        self.assertEqual(descriptor.json()["kind"], "pdf")
        self.assertFalse(descriptor.json()["pageNavigationVerified"])
        self.assertEqual(descriptor.json()["pdfPageRenderer"], "server_pdfium2")
        first = self.client.get(self.url + "1")
        second = self.client.get(self.url + "2")
        self.assertEqual((first.status_code, second.status_code), (200, 200))
        self.assertEqual(first["Content-Type"], "image/webp")
        self.assertEqual(second["X-Rendered-Pdf-Page"], "2")
        self.assertEqual(second["X-Source-Asset-Version"], "4")
        self.assertEqual(second["Cache-Control"], "private, no-store")
        self.assertEqual(second["Cross-Origin-Resource-Policy"], "same-origin")
        red, blue = center_pixel(first.content), center_pixel(second.content)
        self.assertGreater(red[0] - red[2], 150)
        self.assertGreater(blue[2] - blue[0], 150)
        self.assertNotIn(b"not-a-real-drive-id", second.content)
        self.item.refresh_from_db()
        self.assertEqual(self.item.note, "Nguyên văn riêng\n")

    def test_auth_stale_hash_bad_page_size_and_changed_bytes_fail_closed(self):
        self.port.read_range.reset_mock()
        self.assertEqual(self.client.get(self.base + "/pdf-page/4/" + "f"*64 + "/1").status_code, 409)
        self.assertEqual(self.client.get(self.url + "0").status_code, 422)
        self.assertEqual(self.client.get(self.url + "501").status_code, 422)
        self.port.read_range.assert_not_called()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url + "1").status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(self.url + "1").status_code, 401)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.url + "3").status_code, 422)
        self.port.read_range.side_effect = (
            lambda asset, start, end: bytes([self.body[start] ^ 1]) + self.body[start+1:end+1]
        )
        self.assertEqual(self.client.get(self.url + "1").status_code, 409)

    def test_large_pdf_does_not_fetch(self):
        from .pdf_page_render import MAX_PDF_BYTES
        self.asset.size = MAX_PDF_BYTES + 1
        self.asset.save(update_fields=["size"])
        self.port.read_range.reset_mock()
        self.assertEqual(self.client.get(self.url + "1").status_code, 413)
        self.port.read_range.assert_not_called()
