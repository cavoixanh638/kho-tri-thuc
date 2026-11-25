"""Authenticated, version-pinned PDF page raster endpoint.

The returned PNG is rendered from the exact SHA256-verified source bytes.
Unlike an iframe #page fragment, this endpoint proves which PDF page was
actually parsed. Never leaks Drive IDs or embeds a bearer URL.
"""
import hashlib
from contextlib import closing
from io import BytesIO

from django.http import HttpResponse
from ninja import Router
from ninja.security import django_auth
from processing.pdfium_lock import PDFIUM_LOCK

from .drive import DriveError
from .pdf_source_cache import MAX_PDF_BYTES, VerifiedPdfCache
from .viewer_api import MAX_RANGE, error, owned_asset, private, storage_error, supported
from .service import storage_for_owner

router = Router(auth=django_auth, tags=["Private PDF pages"])
_sources = VerifiedPdfCache()
MAX_PDF_PAGES = 2000
MAX_PAGE_PIXELS = 4_000_000
MAX_PNG_BYTES = 5 * 1024 * 1024


@router.get("/assets/{asset_id}/pdf-page/{version}/{sha256}/{page_number}")
def pdf_page(request, asset_id: str, version: int, sha256: str, page_number: int):
    # Authenticate+authorize before parsing a single remote byte.
    asset = owned_asset(request, asset_id)
    if version != asset.content_version or sha256 != asset.sha256:
        return error("viewer_source_changed", 409)
    if asset.mime != "application/pdf" or not supported(asset):
        return error("viewer_not_supported", 409)
    if not 1 <= page_number <= MAX_PDF_PAGES:
        return error("viewer_page_invalid", 422)
    if asset.size > MAX_PDF_BYTES:
        return error("viewer_pdf_too_large", 413)

    try:
        storage = storage_for_owner(request.user.pk)
        # Only an adapter that validates the entire remote identity and SHA on
        # *each* range can replace a full refetch with an authorized byte probe.
        can_probe = getattr(storage, "verifies_range_source", False) is True
        key = (request.user.pk, asset.pk, version, sha256, asset.size)
        source = _sources.get(key) if can_probe else None
        if source is not None:
            if storage.read_range(asset, 0, 0) != source[:1]:
                return error("viewer_source_changed", 409)
        else:
            data = bytearray()
            for offset in range(0, asset.size, MAX_RANGE):
                end = min(offset + MAX_RANGE, asset.size) - 1
                chunk = storage.read_range(asset, offset, end)
                if not isinstance(chunk, bytes) or len(chunk) != end - offset + 1:
                    return error("viewer_range_size_mismatch", 502)
                data.extend(chunk)
            if hashlib.sha256(data).hexdigest() != sha256:
                return error("viewer_source_changed", 409)
            source = bytes(data)
            if can_probe:
                _sources.remember(key, source)
    except DriveError as exc:
        return storage_error(exc)

    try:
        import pypdfium2 as pdfium

        with PDFIUM_LOCK, closing(pdfium.PdfDocument(source)) as pdf:
            if page_number > len(pdf):
                return error("viewer_page_out_of_range", 416)
            page = pdf[page_number - 1]
            try:
                width, height = page.get_size()
                if not (0 < width <= 10000 and 0 < height <= 10000):
                    return error("viewer_pdf_page_dimensions", 422)
                scale = min(1.4, (MAX_PAGE_PIXELS / (width * height)) ** 0.5)
                bitmap = page.render(scale=scale)
                try:
                    image = bitmap.to_pil()
                    try:
                        output = BytesIO()
                        image.save(output, format="PNG", optimize=True)
                        pixels = output.getvalue()
                    finally:
                        image.close()
                finally:
                    bitmap.close()
            finally:
                page.close()
    except (ValueError, RuntimeError, OSError, MemoryError):
        return error("viewer_pdf_unreadable", 422)

    if len(pixels) > MAX_PNG_BYTES:
        return error("viewer_pdf_page_too_large", 413)
    response = private(HttpResponse(pixels, content_type="image/png"))
    response["Content-Disposition"] = 'inline; filename="verified-page.png"'
    response["X-KT-PDF-Page"] = str(page_number)
    response["X-KT-Asset-Version"] = str(version)
    response["X-KT-Source-SHA256"] = asset.sha256
    response["Content-Length"] = str(len(pixels))
    return response
