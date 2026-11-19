import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from . import video_download as parent
from . import video_download_child as child


class VideoURLTests(unittest.TestCase):
    def test_only_supported_facebook_https_urls_are_accepted(self):
        for url in (
            "https://www.facebook.com/share/r/Abc123/",
            "https://facebook.com/reel/12345",
            "https://m.facebook.com/watch/?v=12345",
        ):
            with self.subTest(url=url):
                self.assertTrue(parent.is_facebook_url(url))
        for url in (
            "http://www.facebook.com/reel/123",
            "https://facebook.com:443/reel/123",
            "https://facebook.com.evil.test/reel/123",
            "https://x@facebook.com/reel/123",
            "https://facebook.com/reel/123#fragment",
            "https://facebook.com/reel/x",
            "https://facebook.com/watch?v=123&v=456",
            "https://facebook.com/watch?v=1&x=2",
            "https://facebook.com/share/r/abc/?redirect=http://localhost",
            "https://facebook.com/reel/123\n",
            "https://facebook.com/../reel/123",
        ):
            with self.subTest(url=url):
                self.assertFalse(parent.is_facebook_url(url))

    def test_environment_does_not_pass_credentials_or_proxy(self):
        with patch.dict(
            os.environ,
            {
                "GOOGLE_SECRET": "private",
                "HTTPS_PROXY": "private",
                "PYTHONPATH": "private",
                "SystemRoot": "Windows",
            },
            clear=True,
        ):
            env = parent.child_environment()
        self.assertEqual(
            {key.upper(): value for key, value in env.items()}["SYSTEMROOT"], "Windows"
        )
        self.assertNotIn("GOOGLE_SECRET", env)
        self.assertNotIn("HTTPS_PROXY", env)
        self.assertNotIn("PYTHONPATH", env)


class NetworkGuardTests(unittest.TestCase):
    def test_public_ip_rejects_loopback_link_local_multicast_and_mapped(self):
        for ip in (
            "127.0.0.1",
            "10.0.0.1",
            "169.254.169.254",
            "::1",
            "fe80::1",
            "224.0.0.1",
            "::ffff:8.8.8.8",
        ):
            with self.subTest(ip=ip):
                self.assertFalse(child.public_ip(ip))
        self.assertTrue(child.public_ip("8.8.8.8"))

    def test_dns_and_connect_checks_cannot_be_bypassed_with_private_or_raw_ip(self):
        records = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))]
        with (
            patch.object(socket, "getaddrinfo", return_value=records) as resolve,
            patch.object(socket.socket, "connect") as connect,
            patch.object(socket.socket, "connect_ex") as connect_ex,
        ):
            child.install_network_guard()
            for address in (
                ("127.0.0.1", 443),
                ("8.8.8.8", 443),
                ("www.facebook.com", 443),
            ):
                with self.assertRaises(child.DownloadBlocked):
                    socket.socket.connect(object(), address)
            for host in (
                "localhost",
                "facebook.com.evil.test",
                "8.8.8.8",
                "www.facebook.com.",
            ):
                with self.assertRaises(child.DownloadBlocked):
                    socket.getaddrinfo(host, 443)
            socket.getaddrinfo("www.facebook.com", 443)
            socket.socket.connect(object(), ("8.8.8.8", 443))
            socket.socket.connect_ex(object(), ("8.8.8.8", 443))
            self.assertEqual(connect.call_count, 1)
            self.assertEqual(connect_ex.call_count, 1)
            self.assertEqual(resolve.call_count, 1)
            for address in (("8.8.8.8", 80), ("10.0.0.1", 443)):
                with self.assertRaises(child.DownloadBlocked):
                    socket.socket.connect_ex(object(), address)
            resolve.return_value = [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))
            ]
            with self.assertRaises(child.DownloadBlocked):
                socket.getaddrinfo("www.facebook.com", 443)


class ProgressiveTests(unittest.TestCase):
    def test_selects_hd_and_refuses_external_or_video_only_sources(self):
        def fmt(name, **kwargs):
            return {
                "format_id": name,
                "ext": "mp4",
                "url": "https://video.fbcdn.net/file",
                **kwargs,
            }

        sd, hd = fmt("sd"), fmt("hd")
        self.assertEqual(list(child.select_progressive({"formats": [sd, hd]})), [hd])
        bad = [fmt("hd", acodec="none"), fmt("sd", url="https://example.com/file")]
        with self.assertRaises(child.DownloadBlocked):
            list(child.select_progressive({"formats": bad}))

    def test_writer_refuses_exceeding_quota_before_writing(self):
        stream = io.BytesIO()
        writer = child.BoundedWriter(stream)
        with patch.object(child, "MAX_BYTES", 8):
            writer.write(b"12345")
            with self.assertRaises(child.DownloadBlocked):
                writer.write(b"6789")
        self.assertEqual(stream.getvalue(), b"12345")


class ChildProcessTests(unittest.TestCase):
    def test_real_timeout_kills_child(self):
        with (
            tempfile.TemporaryDirectory() as temp,
            subprocess.Popen(
                [sys.executable, "-c", "import time; time.sleep(30)"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ) as process,
        ):
            with (
                patch.object(parent, "TIMEOUT_SECONDS", 0.05),
                self.assertRaisesRegex(parent.VideoDownloadError, "video_timeout"),
            ):
                parent._wait(process, Path(temp))
            self.assertIsNotNone(process.poll())

    def test_detects_combined_partial_files_above_directory_quota(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / "one.part").write_bytes(b"12345")
            (directory / "two.part").write_bytes(b"12345")
            with subprocess.Popen(
                [sys.executable, "-c", "import time; time.sleep(30)"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ) as process:
                with (
                    patch.object(parent, "MAX_BYTES", 8),
                    patch.object(parent, "MAX_RESULT_BYTES", 0),
                    self.assertRaisesRegex(
                        parent.VideoDownloadError, "video_too_large"
                    ),
                ):
                    parent._wait(process, directory)
                self.assertIsNotNone(process.poll())

    def test_existing_destination_is_preserved_without_starting_child(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "asset"
            path.write_bytes(b"original")
            with (
                patch.object(parent.subprocess, "Popen") as spawn,
                self.assertRaisesRegex(
                    parent.VideoDownloadError, "video_destination_exists"
                ),
            ):
                parent.download_facebook("https://facebook.com/reel/123", path)
            self.assertEqual(path.read_bytes(), b"original")
            spawn.assert_not_called()

    def test_rejects_html_and_invalid_manifest_without_returning_signed_error(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            data = {"status": "failed", "error_code": "https://signed.example/token"}
            (directory / "result.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(
                parent.VideoDownloadError, "^video_download_failed$"
            ):
                parent._result(directory)
            data.update(
                status="done", title="", description="", platform_id="123", duration=10
            )
            (directory / "result.json").write_text(json.dumps(data))
            (directory / "video.mp4").write_bytes(b"<html>not video</html>")
            with self.assertRaisesRegex(
                parent.VideoDownloadError, "video_invalid_output"
            ):
                parent._result(directory)

    def test_success_atomically_moves_fixed_output_and_removes_scratch(self):
        class Done:
            def __init__(self, command, **_kwargs):
                directory = Path(command[-1])
                (directory / "video.mp4").write_bytes(
                    b"\x00\x00\x00\x18ftypisom" + b"data"
                )
                (directory / "result.json").write_text(
                    json.dumps(
                        {
                            "status": "done",
                            "title": "title",
                            "description": "",
                            "platform_id": "123",
                            "duration": 3.0,
                        }
                    )
                )

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def poll(self):
                return 0

            def wait(self, **_kwargs):
                return 0

        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "asset"
            with patch.object(parent.subprocess, "Popen", Done):
                result = parent.download_facebook(
                    "https://facebook.com/reel/123", destination
                )
            self.assertEqual(result.path, destination)
            self.assertEqual(result.platform_id, "123")
            self.assertEqual(list(Path(temp).iterdir()), [destination])
