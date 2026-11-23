"""Private, version-pinned source bytes; no disk cache, tokens or redirects."""

import re
import hashlib
import io
import math
from uuid import UUID

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.security import django_auth

from .drive import DriveError
from .models import Asset, StorageLocation
from .service import DRIVE_PROVIDER, storage_for_owner

router = Router(auth=django_auth, tags=["Private source viewer"])
MAX_RANGE = 4 * 1024 * 1024
MAX_PDF_RENDER_BYTES = 12 * 1024 * 1024
MAX_PDF_RENDER_PAGE = 2000
MEDIA_TYPES = {
    "application/pdf",
    "audio/mpeg",
    "audio/mp4",
    "audio/ogg",
    "audio/wav",
    "audio/x-wav",
    "audio/webm",
    "audio/flac",
    "video/mp4",
    "video/webm",
    "video/ogg",
    "video/quicktime",
}


def private(response):
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    response["Referrer-Policy"] = "no-referrer"
    response["Cross-Origin-Resource-Policy"] = "same-origin"
    response["Vary"] = "Cookie"
    return response


def error(code, status):
    return private(JsonResponse({"code": code}, status=status))


def owned_asset(request, asset_id):
    return get_object_or_404(
        Asset.objects.select_related("item"),
        pk=asset_id,
        item__owner=request.user,
        item__deleted_at__isnull=True,
    )


def supported(asset):
    return bool(
        asset.mime in MEDIA_TYPES
        and type(asset.size) is int
        and asset.size > 0
        and re.fullmatch(r"[a-f0-9]{64}", asset.sha256)
        and asset.locations.filter(
            provider=DRIVE_PROVIDER,
            status=StorageLocation.Status.VERIFIED,
        ).exists()
    )


def storage_error(exc):
    return error(
        "viewer_unavailable" if exc.retryable else "viewer_source_unavailable",
        503 if exc.retryable else 409,
    )


@router.get("/assets/{asset_id}/viewer")
def viewer(request, asset_id: UUID):
    asset = owned_asset(request, asset_id)
    if not supported(asset):
        return error("viewer_not_supported", 409)
    try:
        # An actual one-byte 206 proves this provider/file supports ranges now.
        storage_for_owner(request.user.pk).read_range(asset, 0, 0)
    except DriveError as exc:
        return storage_error(exc)
    return private(
        JsonResponse(
            {
                "assetId": str(asset.pk),
                "version": asset.sha256,
                "assetVersion": asset.content_version,
                "url": f"/api/v1/assets/{asset.pk}/content/{asset.content_version}/{asset.sha256}",
                "kind": "pdf" if asset.mime == "application/pdf" else "media",
                "rangeVerified": True,
                # Native PDF fragment navigation has not been accepted on every host.
                "pageNavigationVerified": asset.mime == "application/pdf"
                and settings.PDF_NATIVE_PAGE_NAVIGATION_VERIFIED,
                **({"pdfPageRenderingVerified": asset.size <= MAX_PDF_RENDER_BYTES}
                   if asset.mime == "application/pdf" else {}),
            }
        )
    )


def selected_range(header, size):
    """Select one bounded byte range without ever lying about an explicit range.

    A client can advance an open-ended range in 4 MiB steps. Explicit closed
    and suffix ranges must be served in full or rejected with HTTP 416: quietly
    truncating a suffix would return the *wrong bytes* for PDF/media seekers.
    """
    if size <= 0:
        raise ValueError("viewer_range_invalid")
    if header is None:
        if size > MAX_RANGE:
            raise ValueError("viewer_range_required")
        return 0, size - 1, False
    match = re.fullmatch(r"bytes=([0-9]{0,20})-([0-9]{0,20})", header)
    if not match or not any(match.groups()):
        raise ValueError("viewer_range_invalid")
    first, last = match.groups()
    if first:
        start = int(first)
        end = min(int(last), size - 1) if last else size - 1
        if start >= size or end < start:
            raise ValueError("viewer_range_invalid")
        if not last:
            # Open-ended requests can be served incrementally by media clients.
            end = min(end, start + MAX_RANGE - 1)
    else:
        suffix = int(last)
        if suffix <= 0:
            raise ValueError("viewer_range_invalid")
        start, end = max(0, size - suffix), size - 1
    if end - start + 1 > MAX_RANGE:
        raise ValueError("viewer_range_too_large")
    return start, end, True


@router.api_operation(["GET", "HEAD"], "/assets/{asset_id}/content/{version}/{sha256}")
def content(request, asset_id: UUID, version: int, sha256: str):
    asset = owned_asset(request, asset_id)
    if version != asset.content_version or sha256 != asset.sha256:
        return error("viewer_source_changed", 409)
    if not supported(asset):
        return error("viewer_not_supported", 409)
    etag = f'"{asset.pk}:{asset.content_version}:{asset.sha256}"'
    # Reject stale conditional requests instead of serving a replacement file.
    if request.headers.get("If-Range") not in (None, etag):
        return error("viewer_source_changed", 412)
    if request.headers.get("If-Match") not in (None, etag, "*"):
        return error("viewer_source_changed", 412)
    try:
        start, end, partial = (
            (0, asset.size - 1, False)
            if request.method == "HEAD" and "Range" not in request.headers
            else selected_range(request.headers.get("Range"), asset.size)
        )
    except ValueError as exc:
        response = error(str(exc), 416)
        response["Content-Range"] = f"bytes */{asset.size}"
        response["Accept-Ranges"] = "bytes"
        response["ETag"] = etag
        return response
    try:
        storage = storage_for_owner(request.user.pk)
        # HEAD validates current remote provenance without fetching the body.
        payload = storage.read_range(
            asset, start, start if request.method == "HEAD" else end
        )
    except DriveError as exc:
        return storage_error(exc)
    # Even an incorrectly configured storage adapter may never produce a 206
    # with a Content-Length that disagrees with the bytes actually returned.
    expected = 1 if request.method == "HEAD" else end - start + 1
    if not isinstance(payload, bytes) or len(payload) != expected:
        return error("viewer_range_size_mismatch", 502)
    response = private(
        HttpResponse(
            b"" if request.method == "HEAD" else payload,
            content_type=asset.mime,
            status=206 if partial else 200,
        )
    )
    response["Accept-Ranges"] = "bytes"
    response["Content-Length"] = str(end - start + 1)
    response["Content-Disposition"] = 'inline; filename="source"'
    response["ETag"] = etag
    if partial:
        response["Content-Range"] = f"bytes {start}-{end}/{asset.size}"
    return response


@router.get("/assets/{asset_id}/pdf-page/{version}/{sha256}/{page}")
def pdf_page(request, asset_id: UUID, version: int, sha256: str, page: int):
    """Render exactly one authenticated, source-version-pinned PDF page.

    This is a deterministic PDFium raster view, not Chrome's unreliable #page
    navigation. No public URL, no remote redirects, and no disk cache. The
    complete source SHA256 is checked before parsing any bytes; the 12 MiB
    document cap keeps byte retrieval and PDF parsing bounded.
    """
    asset = owned_asset(request, asset_id)
    if version != asset.content_version or sha256 != asset.sha256:
        return error("viewer_source_changed", 409)
    if asset.mime != "application/pdf" or not supported(asset):
        return error("viewer_not_supported", 409)
    if not 1 <= page <= MAX_PDF_RENDER_PAGE:
        return error("viewer_pdf_page_out_of_range", 422)
    if asset.size > MAX_PDF_RENDER_BYTES:
        return error("viewer_pdf_too_large", 413)
    try:
        store = storage_for_owner(request.user.pk)
        pieces = []
        digest = hashlib.sha256()
        for start in range(0, asset.size, MAX_RANGE):
            end = min(asset.size - 1, start + MAX_RANGE - 1)
            payload = store.read_range(asset, start, end)
            if not isinstance(payload, bytes) or len(payload) != end - start + 1:
                return error("viewer_range_size_mismatch", 502)
            digest.update(payload)
            pieces.append(payload)
    except DriveError as exc:
        return storage_error(exc)
    if digest.hexdigest() != asset.sha256:
        return error("viewer_source_changed", 409)
    try:
        import pypdfium2 as pdfium

        document = pdfium.PdfDocument(b"".join(pieces))
        try:
            if page > len(document):
                return error("viewer_pdf_page_out_of_range", 422)
            selected = document[page - 1]
            try:
                width, height = selected.get_size()
                if not (math.isfinite(width) and math.isfinite(height)
                        and width > 0 and height > 0):
                    return error("viewer_pdf_dimensions_invalid", 422)
                scale = min(1.5, math.sqrt(1_500_000 / (width * height)))
                if scale <= 0:
                    return error("viewer_pdf_dimensions_invalid", 422)
                bitmap = selected.render(scale=scale)
                try:
                    image = bitmap.to_pil()
                    output = io.BytesIO()
                    image.save(output, format="PNG", optimize=True)
                finally:
                    bitmap.close()
            finally:
                selected.close()
        finally:
            document.close()
    except (ValueError, RuntimeError, OSError, OverflowError, MemoryError):
        return error("viewer_pdf_render_failed", 422)
    response = private(HttpResponse(output.getvalue(), content_type="image/png"))
    response["Content-Disposition"] = 'inline; filename="pdf-page.png"'
    response["X-Source-Page"] = str(page)
    response["X-Source-SHA256"] = asset.sha256
    return response
