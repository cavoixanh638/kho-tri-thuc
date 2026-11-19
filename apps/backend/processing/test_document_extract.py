import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile

from catalog.models import Item
from django.contrib.auth import get_user_model
from django.test import TestCase
from docx import Document
from jobs.models import Job
from openpyxl import Workbook
from pypdf import PdfWriter
from storage.models import Asset

from .document_extract import extract_document, extract_local
from .document_job import extract_from_staging
from .models import DerivedContent


class DocumentExtractionTests(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_docx_and_xlsx_preserve_unicode_and_locators(self):
        docx = self.root / "test.docx"
        document = Document()
        document.add_paragraph("Tri thức tiếng Việt – Đô thị")
        document.add_table(rows=1, cols=1).cell(0, 0).text = "Bảng nội dung"
        document.save(docx)
        result = extract_document(
            docx, mime="application/octet-stream", filename="test.docx"
        )
        self.assertEqual(result["state"], "done")
        self.assertEqual(
            result["parts"][0],
            {
                "text": "Tri thức tiếng Việt – Đô thị",
                "locator": {"block": 1},
            },
        )
        self.assertIn("Bảng nội dung", result["parts"][1]["text"])

        xlsx = self.root / "test.xlsx"
        book = Workbook()
        book.active.title = "Dữ liệu"
        book.active.append(["Mã", "Nội dung"])
        book.active.append(["A01", "Giữ dấu tiếng Việt"])
        book.save(xlsx)
        book.close()
        result = extract_document(
            xlsx, mime="application/octet-stream", filename="test.xlsx"
        )
        self.assertEqual(result["state"], "done")
        self.assertEqual(result["parts"][1]["locator"], {"sheet": "Dữ liệu", "row": 2})
        self.assertIn("B2: Giữ dấu tiếng Việt", result["parts"][1]["text"])

    def test_blank_encrypted_and_malformed_pdf_are_truthful(self):
        pdf = self.root / "test.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.write(pdf)
        result = extract_document(pdf, mime="application/pdf", filename="test.pdf")
        self.assertEqual(result["state"], "not_available")
        writer.encrypt("requires-password")
        writer.write(pdf)
        result = extract_document(pdf, mime="application/pdf", filename="test.pdf")
        self.assertEqual(result["state"], "encrypted")
        pdf.write_bytes(b"malformed")
        self.assertEqual(
            extract_document(pdf, mime="application/pdf", filename="test.pdf")["state"],
            "failed",
        )

    def test_large_expanded_zip_is_rejected(self):
        package = self.root / "oversized.docx"
        with ZipFile(package, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr("document.xml", b" " * (32 * 1024 * 1024 + 1))
        self.assertEqual(
            extract_document(
                package, mime="application/octet-stream", filename="oversized.docx"
            )["state"],
            "failed",
        )

    def test_pdf_fallback_runs_real_pdfium_after_primary_failure(self):
        from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

        pdf = self.root / "fallback.pdf"
        writer = PdfWriter()
        page = writer.add_blank_page(width=200, height=200)
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
        stream.set_data(b"BT /F1 12 Tf 10 100 Td (Real fallback text) Tj ET")
        page[NameObject("/Contents")] = writer._add_object(stream)
        writer.write(pdf)
        original = pdf.read_bytes()
        with patch(
            "processing.document_extract.pdf_parts",
            side_effect=ValueError("fixture parser failure"),
        ):
            result = extract_local(pdf, "application/pdf", "fallback.pdf")
        self.assertEqual(result["state"], "done")
        self.assertEqual(result["processor"], "pypdfium2-fallback")
        self.assertEqual(result["parts"][0]["locator"], {"page": 1})
        self.assertIn("Real fallback text", result["parts"][0]["text"])
        self.assertEqual(pdf.read_bytes(), original)

    def test_pdf_encryption_is_not_bypassed_and_empty_text_uses_fallback(self):
        with (
            patch(
                "processing.document_extract.pdf_parts", return_value=("encrypted", [])
            ),
            patch("processing.document_extract.pdfium_parts") as fallback,
        ):
            result = extract_local(
                self.root / "encrypted.pdf", "application/pdf", "encrypted.pdf"
            )
            self.assertEqual(result["state"], "encrypted")
            fallback.assert_not_called()
        with (
            patch(
                "processing.document_extract.pdf_parts",
                return_value=("done", [{"text": " ", "locator": {"page": 1}}]),
            ),
            patch(
                "processing.document_extract.pdfium_parts",
                return_value=("done", [{"text": "Tiếng Việt", "locator": {"page": 2}}]),
            ),
        ):
            result = extract_local(
                self.root / "empty.pdf", "application/pdf", "empty.pdf"
            )
            self.assertEqual(
                result["parts"], [{"text": "Tiếng Việt", "locator": {"page": 2}}]
            )
            self.assertEqual(result["processor"], "pypdfium2-fallback")

    def test_idempotent_persistence_preserves_note_and_saved_at(self):
        owner = get_user_model().objects.create(username="owner")
        item = Item.objects.create(
            owner=owner, kind=Item.Kind.FILE, note="Chỉnh sửa thủ công"
        )
        source = self.root / "note.txt"
        data = "Nội dung riêng của bản gốc".encode()
        source.write_bytes(data)
        asset = Asset.objects.create(
            item=item,
            mime="text/plain",
            original_filename="note.txt",
            size=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
        )
        for _ in range(2):
            extract_from_staging(asset, source)
        item.refresh_from_db()
        self.assertEqual(item.note, "Chỉnh sửa thủ công")
        self.assertEqual(item.content_extract, "done")
        self.assertEqual(DerivedContent.objects.filter(asset=asset).count(), 1)
        self.assertEqual(Job.objects.filter(item=item, kind="organize").count(), 1)
        self.assertEqual(source.read_bytes(), data)
