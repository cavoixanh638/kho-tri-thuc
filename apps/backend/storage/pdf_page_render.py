"""Render one exact 1-based PDF page in a bounded, disposable child process.

Only generated WebP bytes go to stdout; failures use generic codes and do not
echo PDF content, filenames, URLs, credentials or parser error messages.
"""
from __future__ import annotations

import io
import math
import sys
from contextlib import closing

import pypdfium2 as pdfium

MAX_PDF_BYTES = 12 * 1024 * 1024
MAX_RENDERED_BYTES = 3 * 1024 * 1024
MAX_PIXELS = 4_000_000
MAX_EDGE = 1600
MAX_PAGES = 500


def render_page(source: bytes, index: int) -> bytes:
    """Render only the requested page; never infer the requested page from text."""
    if (
        type(source) is not bytes or len(source) > MAX_PDF_BYTES or not source
        or type(index) is not int or not 1 <= index <= MAX_PAGES
    ):
        raise ValueError("pdf_page_invalid")
    with closing(pdfium.PdfDocument(source)) as document:
        if not 1 <= index <= len(document):
            raise ValueError("pdf_page_out_of_bounds")
        with closing(document[index - 1]) as page:
            width, height = page.get_size()
            if not (math.isfinite(width) and math.isfinite(height)
                    and 0 < width <= 100000 and 0 < height <= 100000):
                raise ValueError("pdf_page_dimensions_invalid")
            scale = min(2.0, MAX_EDGE / max(width, height),
                        math.sqrt(MAX_PIXELS / (width * height)))
            if not math.isfinite(scale) or scale <= 0:
                raise ValueError("pdf_page_dimensions_invalid")
            with closing(page.render(scale=scale, prefer_bgrx=True)) as bitmap:
                with closing(bitmap.to_pil()) as base:
                    with closing(base.convert("RGB")) as rendered:
                        output = io.BytesIO()
                        rendered.save(output, "WEBP", quality=82, method=3)
                        data = output.getvalue()
    if not data or len(data) > MAX_RENDERED_BYTES:
        raise ValueError("pdf_page_image_limit")
    return data


def main() -> int:
    try:
        if len(sys.argv) != 2 or not sys.argv[1].isascii() or not sys.argv[1].isdigit():
            raise ValueError("page_required")
        index = int(sys.argv[1])
        data = sys.stdin.buffer.read(MAX_PDF_BYTES + 1)
        raster = render_page(data, index)
        sys.stdout.buffer.write(raster)
        return 0
    except (ValueError, OSError, RuntimeError, pdfium.PdfiumError):
        sys.stderr.write("pdf_page_unavailable\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
