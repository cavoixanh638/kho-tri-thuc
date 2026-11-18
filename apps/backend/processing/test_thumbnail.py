import os
import shutil
import subprocess
import tempfile
import unittest
from base64 import b64decode
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
from unittest.mock import DEFAULT, patch
from uuid import uuid4

try:
    from PIL import Image

    from .thumbnail import ThumbnailService
except ModuleNotFoundError as error:
    if error.name not in ("PIL", "pypdfium2"):
        raise
    raise unittest.SkipTest("Install processing/requirements-thumbnail.txt") from error


# Synthetic one-page PDF, encrypted by pypdf with test password "thumbnail-test".
_LOCKED_PDF = b64decode(
    "JVBERi0xLjMKJeLjz9MKMSAwIG9iago8PAovUHJvZHVjZXIgPGRiZGRjMmI2NDg+"
    "Cj4+CmVuZG9iagoyIDAgb2JqCjw8Ci9UeXBlIC9QYWdlcwovQ291bnQgMQovS2lk"
    "cyBbIDQgMCBSIF0KPj4KZW5kb2JqCjMgMCBvYmoKPDwKL1R5cGUgL0NhdGFsb2cK"
    "L1BhZ2VzIDIgMCBSCj4+CmVuZG9iago0IDAgb2JqCjw8Ci9UeXBlIC9QYWdlCi9S"
    "ZXNvdXJjZXMgPDwKPj4KL01lZGlhQm94IFsgMC4wIDAuMCAxMjAgODAgXQovUGFy"
    "ZW50IDIgMCBSCj4+CmVuZG9iago1IDAgb2JqCjw8Ci9WIDEKL1IgMgovTGVuZ3Ro"
    "IDQwCi9QIDQyOTQ5NjcyOTIKL0ZpbHRlciAvU3RhbmRhcmQKL08gPGY4Yjk1NjZh"
    "Yjk2Njg5Zjg1NmVkOTc5ODk2OWU4YmI1MDMzNWVmNTUxM2Y3MDQ3OGUzNDQ0YzFi"
    "NTQ0YWI2MWI+Ci9VIDxhN2ZkODE4MTZmYzRhNmE0YzQxODVkNTAzODc0OTg1NzJh"
    "MmE2NjkzNzNkZjFlZTQyYWVjZjAwYWJiZThmMTNlPgo+PgplbmRvYmoKeHJlZgow"
    "IDYKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDE1IDAwMDAwIG4gCjAwMDAw"
    "MDAwNTkgMDAwMDAgbiAKMDAwMDAwMDExOCAwMDAwMCBuIAowMDAwMDAwMTY3IDAw"
    "MDAwIG4gCjAwMDAwMDAyNjAgMDAwMDAgbiAKdHJhaWxlcgo8PAovU2l6ZSA2Ci9S"
    "b290IDMgMCBSCi9JbmZvIDEgMCBSCi9JRCBbIDxlMGQ2MTY1ODI2OTkxZDIzNGEy"
    "NmQzODM2Njg4MDZlZT4gPGUwZDYxNjU4MjY5OTFkMjM0YTI2ZDM4MzY2ODgwNmVl"
    "PiBdCi9FbmNyeXB0IDUgMCBSCj4+CnN0YXJ0eHJlZgo0NzQKJSVFT0YK"
)
_FFMPEG = os.environ.get("KT_THUMBNAIL_TEST_FFMPEG") or shutil.which("ffmpeg")


class ThumbnailTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.cache = self.root / "cache"
        self.service = ThumbnailService(self.cache, max_edge=64)
        self.asset_id = uuid4()

    def _arguments(self, source, mime_type):
        return {
            "asset_id": self.asset_id,
            "content_sha256": sha256(source.read_bytes()).hexdigest(),
            "mime_type": mime_type,
            "source_path": source,
        }

    def _source_image(self):
        source = self.root / "source.png"
        with Image.new("RGBA", (96, 48), (255, 0, 0, 0)) as image:
            image.paste("red", (48, 0, 96, 48))
            image.save(source)
        return source

    def _two_page_pdf(self):
        source = self.root / "two-pages.pdf"
        with (
            Image.new("RGB", (120, 60), "red") as first,
            Image.new("RGB", (60, 120), "blue") as second,
        ):
            first.save(source, save_all=True, append_images=[second])
        return source

    def _assert_color(self, actual, expected):
        for channel, value in zip(actual, expected, strict=True):
            self.assertAlmostEqual(channel, value, delta=30)

    def test_all_eight_exif_orientations_before_resize(self):
        inverse = (
            None,
            Image.Transpose.FLIP_LEFT_RIGHT,
            Image.Transpose.ROTATE_180,
            Image.Transpose.FLIP_TOP_BOTTOM,
            Image.Transpose.TRANSPOSE,
            Image.Transpose.ROTATE_90,
            Image.Transpose.TRANSVERSE,
            Image.Transpose.ROTATE_270,
        )
        corners = (
            ((0, 0, 80, 40), (240, 20, 20), (8, 8)),
            ((80, 0, 160, 40), (20, 240, 20), (56, 8)),
            ((0, 40, 80, 80), (20, 20, 240), (8, 24)),
            ((80, 40, 160, 80), (240, 240, 20), (56, 24)),
        )
        with Image.new("RGB", (160, 80)) as upright:
            for box, color, _ in corners:
                upright.paste(color, box)
            for orientation, transform in enumerate(inverse, 1):
                with self.subTest(orientation=orientation):
                    source = self.root / f"orientation-{orientation}.jpg"
                    exif = Image.Exif()
                    exif[274] = orientation
                    exif[270] = "fixture metadata"
                    encoded = (
                        upright.copy()
                        if transform is None
                        else upright.transpose(transform)
                    )
                    with encoded:
                        encoded.save(source, quality=100, exif=exif)
                    original = source.read_bytes()
                    mtime = source.stat().st_mtime_ns
                    result = self.service.generate(
                        **self._arguments(source, "image/jpeg")
                    )
                    self.assertEqual(result.content_type, "image/webp")
                    with Image.open(result.path) as thumbnail:
                        self.assertEqual(thumbnail.size, (64, 32))
                        self.assertFalse(thumbnail.getexif())
                        for _, color, pixel in corners:
                            self._assert_color(thumbnail.getpixel(pixel), color)
                    self.assertEqual(source.read_bytes(), original)
                    self.assertEqual(source.stat().st_mtime_ns, mtime)

    def test_first_pdf_page_only(self):
        source = self._two_page_pdf()
        source_bytes = source.read_bytes()
        result = self.service.generate(**self._arguments(source, "Application/PDF"))
        with Image.open(result.path) as thumbnail:
            self.assertEqual(thumbnail.size, (64, 32))
            self._assert_color(thumbnail.getpixel((32, 16)), (255, 0, 0))
        self.assertEqual(source.read_bytes(), source_bytes)

    def test_corrupt_and_locked_pdfs_return_placeholder(self):
        for data, reason in (
            (b"%PDF-1.4\ntruncated", "invalid_pdf"),
            (_LOCKED_PDF, "pdf_locked"),
        ):
            with self.subTest(reason=reason):
                source = self.root / f"{reason}.pdf"
                source.write_bytes(data)
                result = self.service.generate(
                    **self._arguments(source, "application/pdf")
                )
                self.assertIsNone(result.path)
                self.assertIsNone(result.content_type)
                self.assertEqual(result.placeholder_reason, reason)
                self.assertEqual(source.read_bytes(), data)
        self.assertFalse(self.cache.exists())

    def test_jpeg_composites_alpha_on_white(self):
        source = self._source_image()
        args = self._arguments(source, "image/png")
        webp = self.service.generate(**args)
        jpeg = ThumbnailService(self.cache, max_edge=64, output_format="jpeg")
        result = jpeg.generate(**args)
        self.assertEqual(result.content_type, "image/jpeg")
        self.assertNotEqual(result.path, webp.path)
        with Image.open(webp.path) as thumbnail:
            self.assertEqual(thumbnail.getpixel((5, 5))[3], 0)
        with Image.open(result.path) as thumbnail:
            self.assertEqual(thumbnail.size, (64, 32))
            self.assertEqual(thumbnail.format, "JPEG")
            self._assert_color(thumbnail.getpixel((5, 5)), (255, 255, 255))
            self._assert_color(thumbnail.getpixel((58, 5)), (255, 0, 0))

    def test_cache_hit_miss_and_forced_rebuild(self):
        source = self._source_image()
        args = self._arguments(source, "image/png")
        digest = args["content_sha256"]
        self.assertIsNone(self.service.get_cached(self.asset_id, digest))
        result = self.service.generate(**args)
        original = source.read_bytes()
        thumbnail = result.path.read_bytes()
        source.unlink()

        same_profile = ThumbnailService(self.cache, max_edge=64)
        self.assertEqual(
            same_profile.get_cached(str(self.asset_id), digest.upper()), result
        )
        self.assertEqual(same_profile.generate(**args), result)
        self.assertIsNone(same_profile.get_cached(uuid4(), digest))
        self.assertIsNone(same_profile.get_cached(self.asset_id, "a" * 64))
        smaller = ThumbnailService(self.cache, max_edge=32)
        self.assertIsNone(smaller.get_cached(self.asset_id, digest))

        result.path.unlink()
        self.assertIsNone(self.service.get_cached(self.asset_id, digest))
        source.write_bytes(original)
        self.assertEqual(self.service.generate(**args), result)
        self.assertEqual(result.path.read_bytes(), thumbnail)

        result.path.write_bytes(b"replace this cached entry")
        self.assertEqual(self.service.generate(**args, force=True), result)
        self.assertEqual(result.path.read_bytes(), thumbnail)
        self.assertEqual(source.read_bytes(), original)

    def test_bad_identity_or_mismatched_bytes_do_not_write(self):
        source = self._source_image()
        args = self._arguments(source, "image/png")
        for override in (
            {"asset_id": "../asset"},
            {"content_sha256": "../digest"},
            {"content_sha256": "0" * 64},
        ):
            with self.subTest(override=override), self.assertRaises(ValueError):
                self.service.generate(**(args | override))
        self.assertFalse(self.cache.exists())

    def test_failed_replace_keeps_existing_cache_and_removes_temporary_file(self):
        source = self._source_image()
        args = self._arguments(source, "image/png")
        result = self.service.generate(**args)
        cached_bytes = result.path.read_bytes()

        def fail_replace(temporary, target):
            self.assertEqual(temporary.parent, target.parent)
            with Image.open(temporary) as prepared:
                self.assertEqual(prepared.size, (64, 32))
            self.assertEqual(target.read_bytes(), cached_bytes)
            raise PermissionError("synthetic publication failure")

        with (
            patch("processing.thumbnail.os.replace", side_effect=fail_replace),
            self.assertRaises(PermissionError),
        ):
            self.service.generate(**args, force=True)
        self.assertEqual(result.path.read_bytes(), cached_bytes)
        self.assertEqual(list(result.path.parent.iterdir()), [result.path])

    def test_transient_windows_sharing_violation_is_retried(self):
        source = self._source_image()
        args = self._arguments(source, "image/png")
        initial = self.service.generate(**args)
        replace = os.replace
        sharing_error = PermissionError("synthetic Windows sharing violation")
        sharing_error.winerror = 32

        with patch("processing.thumbnail.os.replace", wraps=replace) as publish:
            publish.side_effect = (sharing_error, DEFAULT)
            self.assertEqual(self.service.generate(**args, force=True), initial)
            self.assertEqual(publish.call_count, 2)
        self.assertEqual(list(initial.path.parent.iterdir()), [initial.path])

    def test_concurrent_pdf_writers_leave_a_single_complete_cache_entry(self):
        source = self._two_page_pdf()
        args = self._arguments(source, "application/pdf")
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(self.service.generate, **args, force=True)
                for _ in range(4)
            ]
            results = [future.result() for future in futures]
        path = results[0].path
        self.assertTrue(all(result.path == path for result in results))
        self.assertEqual(list(path.parent.iterdir()), [path])
        with Image.open(path) as thumbnail:
            thumbnail.load()
            self.assertEqual(thumbnail.size, (64, 32))

    def test_video_fallbacks_and_subprocess_limits(self):
        source = self.root / "broken.mp4"
        source.write_bytes(b"invalid video")
        args = self._arguments(source, "video/mp4")
        missing = ThumbnailService(self.cache, ffmpeg=self.root / "missing-ffmpeg.exe")
        self.assertEqual(
            missing.generate(**args).placeholder_reason, "ffmpeg_unavailable"
        )
        with patch(
            "processing.thumbnail_video.subprocess.run",
            side_effect=subprocess.TimeoutExpired("ffmpeg", 15),
        ) as run:
            result = self.service.generate(**args)
        self.assertEqual(result.placeholder_reason, "video_timeout")
        self.assertIsNone(result.path)
        self.assertEqual(run.call_args.kwargs["timeout"], 15)
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("-protocol_whitelist") + 1], "file")
        self.assertEqual(command[command.index("-frames:v") + 1], "1")
        self.assertEqual(command[command.index("-max_pixels") + 1], "33554432")
        self.assertFalse(self.cache.exists())
        self.assertEqual(source.read_bytes(), b"invalid video")

    @unittest.skipUnless(_FFMPEG, "FFmpeg is required for the video smoke test")
    def test_video_frame_from_real_ffmpeg(self):
        source = self.root / "video fixture.mp4"
        subprocess.run(
            [
                _FFMPEG,
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "color=c=red:s=320x180:r=1",
                "-frames:v",
                "1",
                "-c:v",
                "mpeg4",
                str(source),
            ],
            timeout=15,
            check=True,
        )
        service = ThumbnailService(self.cache, max_edge=64, ffmpeg=_FFMPEG)
        original = source.read_bytes()
        result = service.generate(**self._arguments(source, "video/mp4"))
        self.assertIsNone(result.placeholder_reason)
        with Image.open(result.path) as thumbnail:
            self.assertEqual(thumbnail.size, (64, 36))
            self._assert_color(thumbnail.getpixel((32, 18)), (255, 0, 0))
        self.assertEqual(source.read_bytes(), original)

        for data in (
            b"invalid video",
            b"ffconcat version 1.0\nfile 'video fixture.mp4'\n",
        ):
            with self.subTest(data=data):
                invalid = self.root / "invalid.mp4"
                invalid.write_bytes(data)
                fallback = service.generate(**self._arguments(invalid, "video/mp4"))
                self.assertEqual(fallback.placeholder_reason, "invalid_video")
                self.assertIsNone(fallback.path)
