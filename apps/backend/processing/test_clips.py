import hashlib
import io
from types import SimpleNamespace
from unittest.mock import patch

from catalog.models import Item
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from ingestion.models import CaptureEvent
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from storage.models import Asset

from .clips import anchor
from .models import ClipAnnotation, DerivedContent


def fetched(text):
    return SimpleNamespace(
        status="fetched",
        text=text,
        metadata=SimpleNamespace(title="Nguồn công khai tổng hợp"),
        provenance=SimpleNamespace(
            processor="public_web",
            processor_version="test-1",
            body_sha256=hashlib.sha256(text.encode()).hexdigest(),
        ),
    )


def pdf_bytes(text):
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject(
                {NameObject("/F1"): writer._add_object(font)}
            )
        }
    )
    stream = DecodedStreamObject()
    stream.set_data(f"BT /F1 12 Tf 40 700 Td ({text}) Tj ET".encode("ascii"))
    page[NameObject("/Contents")] = writer._add_object(stream)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


class ClipJourneyTests(TransactionTestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="clip-owner")
        self.other = get_user_model().objects.create_user(username="clip-other")
        self.client.force_login(self.owner)

    def post(self, path, body, key=None):
        return self.client.post(
            "/api/v1" + path,
            body,
            content_type="application/json",
            headers={"Idempotency-Key": key} if key else {},
        )

    def preview(self, item, **values):
        return self.post(
            "/clips/preview",
            {
                "target_item_id": str(item.pk),
                "mode": "selection",
                **values,
            },
        )

    def test_twenty_web_selection_anchors_ten_existing_notes_and_receipt_retry(self):
        with patch("processing.clips.fetch_source") as fetch:
            for index in range(20):
                raw = f"# Bài {index} Tiếng Việt\r\nGiữ **nguyên văn**  \r\n"
                item = Item.objects.create(owner=self.owner, kind="text", note=raw)
                quote = f"Tiếng Việt ế nguồn {index} cần kiểm chứng."
                text = f"Phần đầu {index}\n{quote}\nPhần cuối"
                fetch.return_value = fetched(text)
                preview = self.preview(
                    item, url=f"https://example.org/fixture/{index}", quote=quote
                )
                self.assertEqual(preview.status_code, 200, preview.content)
                self.assertEqual(preview.json()["verification"], "current")
                self.assertEqual(
                    Item.objects.get(pk=item.pk).note.encode(), raw.encode()
                )
                receipt = preview.json()["receipt"]
                result = self.post("/clips", {"receipt": receipt}, f"clip-{index}")
                self.assertEqual(result.status_code, 201, result.content)
                repeated = self.post("/clips", {"receipt": receipt}, f"clip-{index}")
                self.assertEqual(repeated.status_code, 200)
                self.assertEqual(
                    repeated.json()["capture_id"], result.json()["capture_id"]
                )
                row = ClipAnnotation.objects.get(pk=result.json()["annotation_id"])
                self.assertEqual(CaptureEvent.objects.filter(item=item).count(), 1)
                self.assertEqual(CaptureEvent.objects.get(item=item).raw_text, quote)
                self.assertEqual(
                    row.quote_hash, hashlib.sha256(quote.encode()).hexdigest()
                )
                excerpt = self.client.get(f"/api/v1/clips/{row.pk}/source")
                self.assertEqual(excerpt.json()["quote"], quote)
                self.assertEqual(
                    row.part.text[row.locator["text_start"] : row.locator["text_end"]],
                    quote,
                )
                self.assertEqual(Item.objects.get(pk=item.pk).note, raw)
                # Another deliberate submission is a new Event on the same Item.
                if index < 10:
                    again = self.post(
                        "/clips", {"receipt": receipt}, f"clip-{index}-new"
                    )
                    self.assertEqual(again.status_code, 201)
                    self.assertNotEqual(
                        again.json()["capture_id"], result.json()["capture_id"]
                    )
                    self.assertEqual(again.json()["item_id"], str(item.pk))
                if index == 0:
                    inserted = self.post(
                        f"/clips/{row.pk}/insert", {"expected_edit_version": 0}
                    )
                    self.assertEqual(inserted.status_code, 200, inserted.content)
                    self.assertTrue(
                        inserted.json()["note"].startswith(raw + "\r\n\r\n")
                    )
                    self.assertEqual(
                        self.post(
                            f"/clips/{row.pk}/insert", {"expected_edit_version": 1}
                        ).status_code,
                        409,
                    )
                row.part.status = "stale"
                row.part.save(update_fields=["status"])
                stale = self.client.get(f"/api/v1/clips/{row.pk}/source")
                self.assertEqual(stale.status_code, 409)
                self.assertEqual(stale.json()["state"], "stale")
            self.assertEqual(Item.objects.count(), 20)
            self.assertEqual(CaptureEvent.objects.count(), 30)

    def test_ten_actual_pdf_extractions_capture_exact_quotes_and_stale_hash(self):
        for index in range(10):
            quote = f"Evidence paragraph {index} keeps a precise source anchor."
            payload = pdf_bytes("Before " + quote + " After")
            text = PdfReader(io.BytesIO(payload)).pages[0].extract_text()
            self.assertIn(quote, text)
            item = Item.objects.create(
                owner=self.owner, kind="file", note=f"Ghi chú {index}\r\n"
            )
            asset = Asset.objects.create(
                item=item,
                original_filename=f"synthetic-{index}.pdf",
                mime="application/pdf",
                size=len(payload),
                sha256=hashlib.sha256(payload).hexdigest(),
            )
            part = DerivedContent.objects.create(
                item=item,
                asset=asset,
                kind="pdf_text",
                text=text,
                input_hash=asset.sha256,
                processor="pypdf",
                processor_version="fixture-1",
                source_locator={"page": 1},
            )
            response = self.preview(item, derived_id=part.pk, quote=quote)
            self.assertEqual(response.status_code, 200, response.content)
            self.assertEqual(response.json()["locator"]["page"], 1)
            result = self.post(
                "/clips", {"receipt": response.json()["receipt"]}, f"pdf-{index}"
            )
            self.assertEqual(result.status_code, 201, result.content)
            self.assertEqual(CaptureEvent.objects.filter(item=item).count(), 1)
            excerpt = self.client.get(
                f"/api/v1/clips/{result.json()['annotation_id']}/source"
            )
            self.assertEqual(excerpt.json()["quote"], quote)
            self.assertEqual(Item.objects.get(pk=item.pk).note, f"Ghi chú {index}\r\n")
            asset.sha256 = "b" * 64
            asset.save(update_fields=["sha256"])
            self.assertEqual(
                self.client.get(
                    f"/api/v1/clips/{result.json()['annotation_id']}/source"
                ).status_code,
                409,
            )

    def test_blocked_and_ambiguous_sources_are_never_reported_verified(self):
        item = Item.objects.create(owner=self.owner, kind="text", note="Bản gốc")
        with patch("processing.clips.fetch_source", return_value=fetched("Lặp Lặp")):
            response = self.preview(
                item, url="https://example.org/repeated", quote="Lặp"
            )
            self.assertEqual(response.json()["verification"], "unverified")
        failed = SimpleNamespace(status="blocked", text=None, metadata=None)
        with patch("processing.clips.fetch_source", return_value=failed):
            response = self.preview(
                item, url="http://127.0.0.1/private", quote="Không được bịa"
            )
            self.assertEqual(response.status_code, 422)
            response = self.preview(
                item, url="https://example.org/blocked", quote="Không được bịa"
            )
            self.assertEqual(response.json()["verification"], "unverified")
            self.assertEqual(response.json()["quote"], "Không được bịa")
        for bad in (
            "javascript:alert(1)",
            "https://user:password@example.org",
            "https://example.org/?access_token=private",
        ):
            self.assertEqual(self.preview(item, url=bad, quote="x").status_code, 422)
        self.assertIsNone(anchor("same same", "same"))
        self.assertEqual(anchor("same same", "same", 5, 9)["text_start"], 5)
        self.assertEqual(CaptureEvent.objects.count(), 0)

    def test_owner_tamper_stale_preview_and_deleted_target_write_nothing(self):
        item = Item.objects.create(owner=self.owner, kind="text", note="Nguyên bản")
        part = DerivedContent.objects.create(
            item=item,
            kind="web_text",
            text="Một đoạn nguồn",
            input_hash="a" * 64,
            processor="fixture",
            processor_version="1",
        )
        response = self.preview(
            item, derived_id=part.pk, url="https://example.org/source", quote="đoạn"
        )
        self.assertEqual(response.status_code, 200, response.content)
        receipt = response.json()["receipt"]
        self.client.force_login(self.other)
        self.assertEqual(
            self.post("/clips", {"receipt": receipt}, "owner-test").status_code, 404
        )
        self.assertEqual(
            self.client.get(f"/api/v1/items/{item.pk}/clips").status_code, 404
        )
        self.client.force_login(self.owner)
        self.assertEqual(
            self.post(
                "/clips", {"receipt": receipt + "tampered"}, "tamper"
            ).status_code,
            422,
        )
        part.status = "stale"
        part.save(update_fields=["status"])
        self.assertEqual(
            self.post("/clips", {"receipt": receipt}, "stale").status_code, 409
        )
        self.assertEqual(CaptureEvent.objects.count(), 0)
        self.assertEqual(ClipAnnotation.objects.count(), 0)
        self.client.logout()
        self.assertEqual(
            self.preview(item, url="https://example.org", quote="x").status_code, 401
        )
