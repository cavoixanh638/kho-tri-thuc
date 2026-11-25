"""Bounded baseline text extraction in a disposable child process."""

import json
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

from .pdfium_lock import PDFIUM_LOCK

MAX_PARTS = 1000
MAX_TEXT = 1_000_000
MAX_EXPANDED = 32 * 1024 * 1024
PROCESSOR_VERSION = "light-documents-v3"


def checked_zip(path):
    with ZipFile(path) as archive:
        entries = archive.infolist()
        if (
            len(entries) > 5000
            or sum(entry.file_size for entry in entries) > MAX_EXPANDED
        ):
            raise ValueError("expanded_document_too_large")


def pdf_parts(path):
    from pypdf import PdfReader

    reader = PdfReader(path)
    if reader.is_encrypted and not reader.decrypt(""):
        return "encrypted", []
    return (
        "partial" if len(reader.pages) > 200 else "done",
        [
            {"text": page.extract_text() or "", "locator": {"page": number}}
            for number, page in enumerate(reader.pages[:200], start=1)
        ],
    )


def pdfium_parts(path):
    import pypdfium2 as pdfium

    parts = []
    with PDFIUM_LOCK, pdfium.PdfDocument(path) as document:
        state = "partial" if len(document) > 200 else "done"
        for index in range(min(len(document), 200)):
            page = document[index]
            text_page = None
            try:
                text_page = page.get_textpage()
                parts.append(
                    {
                        "text": text_page.get_text_bounded(),
                        "locator": {"page": index + 1},
                    }
                )
            finally:
                if text_page is not None:
                    text_page.close()
                page.close()
    return state, parts


def extract_pdf(path):
    try:
        state, parts = pdf_parts(path)
    except Exception:  # noqa: BLE001 - untrusted parser; outer child still enforces timeout
        state, parts = "failed", []
    if state == "encrypted" or any(part["text"].strip() for part in parts):
        return state, parts, "pypdf-baseline"
    state, parts = pdfium_parts(path)
    return state, parts, "pypdfium2-fallback"


def docx_parts(path):
    from docx import Document
    from docx.table import Table

    checked_zip(path)
    parts = []
    for number, block in enumerate(Document(path).iter_inner_content(), start=1):
        if number > MAX_PARTS:
            return "partial", parts
        if isinstance(block, Table):
            text = "\n".join(
                "\t".join(cell.text for cell in row.cells) for row in block.rows
            )
        else:
            text = block.text
        parts.append({"text": text, "locator": {"block": number}})
    return "done", parts


def xlsx_parts(path):
    from openpyxl import load_workbook

    checked_zip(path)
    book = load_workbook(path, read_only=True, data_only=True, keep_links=False)
    parts = []
    cells_seen = 0
    try:
        for sheet in book:
            for row_number, row in enumerate(sheet.iter_rows(), start=1):
                cells_seen += len(row)
                if len(parts) >= MAX_PARTS or cells_seen > 100_000:
                    return "partial", parts
                values = [
                    f"{cell.coordinate}: {cell.value}"
                    for cell in row
                    if cell.value is not None
                ]
                if values:
                    parts.append(
                        {
                            "text": "\t".join(values),
                            "locator": {"sheet": sheet.title, "row": row_number},
                        }
                    )
        return "done", parts
    finally:
        book.close()


def extract_local(path, mime, filename):
    extension = Path(filename).suffix.casefold()
    if mime == "application/pdf" or extension == ".pdf":
        state, parts, processor = extract_pdf(path)
    elif (
        mime
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        or extension == ".docx"
    ):
        state, parts = docx_parts(path)
        processor = "python-docx"
    elif (
        mime == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        or extension == ".xlsx"
    ):
        state, parts = xlsx_parts(path)
        processor = "openpyxl"
    elif mime in {"text/plain", "text/markdown", "text/x-markdown"} or extension in {
        ".md",
        ".markdown",
        ".txt",
    }:
        raw = path.read_bytes()[: MAX_TEXT * 4 + 1]
        text = raw.decode("utf-8-sig")
        state = "partial" if len(text) > MAX_TEXT else "done"
        parts = [{"text": text, "locator": {}}]
        processor = (
            "utf-8-markdown"
            if mime in {"text/markdown", "text/x-markdown"}
            or extension in {".md", ".markdown"}
            else "utf-8"
        )
    else:
        return {"state": "not_available", "parts": [], "processor": "unsupported"}

    bounded = []
    used = 0
    for part in parts[:MAX_PARTS]:
        text = part["text"].replace("\x00", "")
        remaining = MAX_TEXT - used
        if len(text) > remaining:
            text = text[:remaining]
            state = "partial"
        used += len(text)
        if text.strip():
            bounded.append({"text": text, "locator": part["locator"]})
        if used >= MAX_TEXT:
            state = "partial"
            break
    if not bounded and state in ("done", "partial"):
        state = "not_available"
    return {"state": state, "parts": bounded, "processor": processor}


def extract_document(path, *, mime, filename):
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "processing.document_extract",
                str(path),
                mime,
                filename,
            ],
            check=True,
            capture_output=True,
            timeout=45,
            encoding="utf-8",
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        return json.loads(result.stdout)
    except (OSError, ValueError, subprocess.SubprocessError):
        return {"state": "failed", "parts": [], "processor": "light-documents"}


def main():
    try:
        result = extract_local(Path(sys.argv[1]), sys.argv[2], sys.argv[3])
    except Exception:  # noqa: BLE001 - child boundary returns only a safe failure state
        result = {"state": "failed", "parts": [], "processor": "light-documents"}
    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
