"""Generate rebuildable thumbnails from local, immutable staging files."""

import hashlib
import math
import os
import re
import stat
import tempfile
import time
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import BinaryIO, Literal
from uuid import UUID

import pypdfium2 as pdfium
from PIL import Image, ImageOps

from .pdfium_lock import PDFIUM_LOCK
from .thumbnail_video import VideoThumbnailError, read_video_frame

ThumbnailFormat = Literal["webp", "jpeg"]

# Bump when a change makes existing thumbnails stale.
_CACHE_VERSION = "v1"
_OUTPUTS = {"webp": (".webp", "WEBP"), "jpeg": (".jpg", "JPEG")}
_MAX_IMAGE_PIXELS = 64_000_000
_CACHE_WRITE_LOCK = Lock()


@dataclass(frozen=True)
class ThumbnailResult:
    """A local thumbnail or a reason for the caller to show a placeholder."""

    path: Path | None
    content_type: str | None
    placeholder_reason: str | None = None


class _Placeholder(Exception):
    pass


class ThumbnailService:
    """Keep disposable derivatives under the caller's private cache root."""

    def __init__(
        self,
        cache_root: str | Path,
        *,
        max_edge: int = 512,
        output_format: ThumbnailFormat = "webp",
        ffmpeg: str | Path = "ffmpeg",
    ) -> None:
        if type(max_edge) is not int or not 1 <= max_edge <= 2048:
            raise ValueError("max_edge must be an integer from 1 to 2048")
        if output_format not in _OUTPUTS:
            raise ValueError("output_format must be webp or jpeg")
        self.cache_root = Path(cache_root).resolve()
        self.max_edge = max_edge
        self.output_format = output_format
        self.ffmpeg = ffmpeg

    def get_cached(
        self, asset_id: UUID | str, content_sha256: str
    ) -> ThumbnailResult | None:
        """Look up a thumbnail without opening or downloading its source."""
        return self._read_cache(self._cache_path(asset_id, content_sha256))

    def generate(
        self,
        *,
        asset_id: UUID | str,
        content_sha256: str,
        mime_type: str,
        source_path: str | Path,
        force: bool = False,
    ) -> ThumbnailResult:
        """Generate on miss, or replace atomically when force is true.

        The staging file must stay available and immutable for this call.
        An input hash mismatch raises ValueError. Filesystem failures
        propagate as OSError so the worker can retry them.
        """
        target = self._cache_path(asset_id, content_sha256)
        if not force:
            cached = self._read_cache(target)
            if cached is not None:
                return cached

        media_type = mime_type.split(";", 1)[0].strip().lower()
        if not (
            media_type == "application/pdf"
            or media_type.startswith(("image/", "video/"))
        ):
            return ThumbnailResult(None, None, "unsupported_media")

        source = Path(source_path).resolve()
        if source == target:
            raise ValueError("source_path is a thumbnail cache entry")
        try:
            with source.open("rb") as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() != target.stem:
                    raise ValueError("staging file does not match content_sha256")
                stream.seek(0)
                if media_type == "application/pdf":
                    image = _read_pdf(stream, self.max_edge)
                elif media_type.startswith("image/"):
                    image = _read_image(stream)
                else:
                    image = read_video_frame(source, self.max_edge, self.ffmpeg)
        except (_Placeholder, VideoThumbnailError) as error:
            return ThumbnailResult(None, None, str(error))

        try:
            self._write_cache(target, image)
        finally:
            image.close()
        return ThumbnailResult(target, f"image/{self.output_format}")

    def _cache_path(self, asset_id: UUID | str, content_sha256: str) -> Path:
        asset_uuid = UUID(str(asset_id))
        digest = content_sha256.lower()
        if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError("content_sha256 must be a SHA-256 hex digest")
        extension, _ = _OUTPUTS[self.output_format]
        return (
            self.cache_root
            / f"{_CACHE_VERSION}-{self.max_edge}"
            / asset_uuid.hex
            / f"{digest}{extension}"
        )

    def _read_cache(self, target: Path) -> ThumbnailResult | None:
        try:
            info = target.stat()
        except FileNotFoundError:
            return None
        if stat.S_ISREG(info.st_mode) and info.st_size > 0:
            return ThumbnailResult(target, f"image/{self.output_format}")
        return None

    def _write_cache(self, target: Path, image: Image.Image) -> None:
        _, format_name = _OUTPUTS[self.output_format]
        image.thumbnail((self.max_edge, self.max_edge), Image.Resampling.LANCZOS)
        image.info.clear()
        if self.output_format == "jpeg" and image.mode == "RGBA":
            with (
                Image.new("RGB", image.size, "white") as background,
                image.getchannel("A") as alpha,
            ):
                background.paste(image, mask=alpha)
                _write_thumbnail(target, background, format_name)
        else:
            _write_thumbnail(target, image, format_name)


def _write_thumbnail(target: Path, image: Image.Image, format_name: str) -> None:
    with _CACHE_WRITE_LOCK:
        target.parent.mkdir(parents=True, exist_ok=True)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                dir=target.parent, prefix=".thumbnail-", delete=False
            ) as temporary:
                temp_path = Path(temporary.name)
                image.save(temporary, format=format_name, quality=85)
            _publish(temp_path, target)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)


def _publish(temporary: Path, target: Path) -> None:
    # Windows can deny a replace while another process briefly holds the target.
    for delay in (0.01, 0.02, 0.04, 0.08):
        try:
            os.replace(temporary, target)
            return
        except PermissionError as error:
            if getattr(error, "winerror", None) not in (5, 32):
                raise
            time.sleep(delay)
    os.replace(temporary, target)


def _read_image(stream: BinaryIO) -> Image.Image:
    try:
        with Image.open(stream) as image:
            if image.width * image.height > _MAX_IMAGE_PIXELS:
                raise _Placeholder("image_too_large")
            ImageOps.exif_transpose(image, in_place=True)
            return image.convert("RGBA" if image.has_transparency_data else "RGB")
    except Image.DecompressionBombError as error:
        raise _Placeholder("image_too_large") from error
    except (OSError, SyntaxError, ValueError) as error:
        if isinstance(error, OSError) and error.errno is not None:
            raise
        raise _Placeholder("invalid_image") from error


def _read_pdf(stream: BinaryIO, max_edge: int) -> Image.Image:
    # PDFium calls, including handle cleanup, must be serialized in a process.
    try:
        with PDFIUM_LOCK, closing(pdfium.PdfDocument(stream)) as document:
            if len(document) == 0:
                raise _Placeholder("invalid_pdf")
            with closing(document[0]) as page:
                width, height = page.get_size()
                if not (0 < width < math.inf and 0 < height < math.inf):
                    raise _Placeholder("invalid_pdf")
                scale = max_edge / max(width, height)
                with (
                    closing(page.render(scale=scale, prefer_bgrx=True)) as bitmap,
                    bitmap.to_pil() as image,
                ):
                    return image.convert("RGB")
    except pdfium.PdfiumError as error:
        if error.err_code == pdfium.raw.FPDF_ERR_PASSWORD:
            raise _Placeholder("pdf_locked") from error
        raise _Placeholder("invalid_pdf") from error
