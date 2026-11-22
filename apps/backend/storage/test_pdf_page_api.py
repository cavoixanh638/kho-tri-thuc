"""P08/J6B: exact page pixels from authenticated pinned PDF bytes."""
import hashlib
from io import BytesIO
from unittest.mock import patch

from PIL import Image
from catalog.models import Item
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .models import Asset, StorageLocation
from .pdf_page_api import MAX_PDF_BYTES


def pdf_fixture():
    """Three colored pages generated entirely in memory; page 2 is green."""
    objects = ["<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>", None]
    page_ids = []
    colors = ("1 0 0", "0 1 0", "0 0 1")
    for number, color in enumerate(colors, 1):
        stream = color + " rg 0 0 612 792 re f\n1 1 1 rg BT /F1 30 Tf 50 600 Td (PAGE " + str(number) + ") Tj ET"
        data = stream.encode("ascii")
        objects.append("<< /Length " + str(len(data)) + " >>\nstream\n" + stream + "\nendstream")
        stream_id = len(objects)
        objects.append("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 1 0 R >> >> /Contents " + str(stream_id) + " 0 R >>")
        page_ids.append(len(objects))
    objects[1] = "<< /Type /Pages /Kids [" + " ".join(str(idx) + " 0 R" for idx in page_ids) + "] /Count 3 >>"
    objects.append("<< /Type /Catalog /Pages 2 0 R >>")
    result = b"%PDF-1.4\n"
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(result))
        result += (str(index) + " 0 obj\n" + obj + "\nendobj\n").encode("ascii")
    xref = len(result)
    result += ("xref\n0 " + str(len(objects) + 1) + "\n0000000000 65535 f \n").encode("ascii")
    for off in offsets[1:]:
        result += (str(off).zfill(10) + " 00000 n \n").encode("ascii")
    result += ("trailer\n<< /Size " + str(len(objects) + 1)
               + " /Root " + str(len(objects)) + " 0 R >>\nstartxref\n"
               + str(xref) + "\n%%EOF\n").encode("ascii")
    return result


class PrivatePdfPageTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="pdf-qa-owner")
        self.other = get_user_model().objects.create_user(username="pdf-qa-other")
        self.note = "# Giữ nguyên bản biên soạn"
        self.item = Item.objects.create(owner=self.owner, kind="file", note=self.note)
        self.body = pdf_fixture()
        self.digest = hashlib.sha256(self.body).hexdigest()
        self.asset = Asset.objects.create(
            item=self.item, mime="application/pdf", size=len(self.body),
            sha256=self.digest, content_version=2, original_filename="test-generated.pdf",
        )
        StorageLocation.objects.create(
            asset=self.asset, provider="google_drive",
            provider_file_id="fixture-private-pdf-owner-only",
            status="verified", verified_at=timezone.now(),
        )
        self.path = ("/api/v1/assets/" + str(self.asset.pk) + "/pdf-page/2/"
                     + self.digest + "/2")
        self.client.force_login(self.owner)
        patcher = patch("storage.pdf_page_api.storage_for_owner")
        self.mock = patcher.start()
        self.addCleanup(patcher.stop)
        self.calls = []

        def read_range(asset, start, end):
            self.calls.append((start, end))
            return self.body[start:end + 1]

        self.mock.return_value.read_range.side_effect = read_range

    def test_page_two_is_green_after_actual_pdfium_render(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200, response.content[:100])
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-KT-PDF-Page"], "2")
        self.assertEqual(response["X-KT-Asset-Version"], "2")
        self.assertEqual(response["X-KT-Source-SHA256"], self.digest)
        self.assertNotIn("fixture-private-pdf", str(response.headers))
        self.assertEqual(self.calls, [(0, len(self.body) - 1)])
        with Image.open(BytesIO(response.content)) as image:
            self.assertGreater(image.width, 200)
            self.assertGreater(image.height, 200)
            rgb = image.convert("RGB")
            center = rgb.getpixel((rgb.width // 2, rgb.height // 2))
            self.assertGreater(center[1], 240, center)
            self.assertLess(center[0], 20, center)
            self.assertLess(center[2], 20, center)
        self.assertEqual(Item.objects.get(pk=self.item.pk).note, self.note)

    def test_unauthorized_stale_and_wrong_page_fail_before_read(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.path).status_code, 404)
        self.client.logout()
        self.assertIn(self.client.get(self.path).status_code, (401, 403))
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.path.replace("/pdf-page/2/", "/pdf-page/1/")).status_code, 409)
        self.assertEqual(self.client.get(self.path.replace(self.digest, "a" * 64)).status_code, 409)
        # Authorization and stale-version failures must reject without reads.
        self.assertFalse(self.calls)
        # Page number 4 is outside the *parsed* three-page PDF, so the
        # backend must read+verify bytes before it can know the page count.
        self.assertEqual(self.client.get(self.path[:-1] + "4").status_code, 416)
        self.assertEqual(self.calls, [(0, len(self.body) - 1)])

    def test_corruption_and_malformed_bytes_cannot_pass_verified_page(self):
        self.mock.return_value.read_range.side_effect = lambda *_: b"0" * len(self.body)
        self.assertEqual(self.client.get(self.path).status_code, 409)
        self.mock.return_value.read_range.side_effect = lambda *_: b"short"
        self.assertEqual(self.client.get(self.path).status_code, 502)
        self.mock.return_value.read_range.side_effect = lambda a, s, e: self.body[s:e + 1]
        self.asset.size = MAX_PDF_BYTES + 1
        self.asset.save(update_fields=["size"])
        self.assertEqual(self.client.get(self.path).status_code, 413)

    def test_pending_location_and_wrong_mime_cannot_claim_page(self):
        location = self.asset.locations.get()
        location.status = "pending"
        location.save(update_fields=["status"])
        self.assertEqual(self.client.get(self.path).status_code, 409)
        location.status = "verified"
        location.save(update_fields=["status"])
        self.asset.mime = "video/mp4"
        self.asset.save(update_fields=["mime"])
        self.assertEqual(self.client.get(self.path).status_code, 409)
