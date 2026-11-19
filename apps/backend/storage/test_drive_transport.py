from io import BytesIO
from unittest.mock import Mock, patch

import httplib2
from django.test import SimpleTestCase
from google.auth.credentials import AnonymousCredentials

from .drive import DriveClient, DriveError


class DriveTransportTests(SimpleTestCase):
    def test_real_transport_accepts_resume_308_without_redirect_location(self):
        client = DriveClient(AnonymousCredentials())
        replies = [
            (
                httplib2.Response(
                    {
                        "status": "200",
                        "location": "https://www.googleapis.com/upload/drive/v3/files?upload_id=fixture",
                    }
                ),
                b"",
            ),
            (httplib2.Response({"status": "308", "range": "bytes=0-1048575"}), b""),
            (
                httplib2.Response(
                    {"status": "200", "content-type": "application/json"}
                ),
                b'{"id":"fixture-file"}',
            ),
        ]
        with patch.object(
            client.api._http.http, "_conn_request", side_effect=replies
        ) as send:
            result = client.upload_blob(
                BytesIO(b"x" * (2 * 1024 * 1024)),
                "video/mp4",
                {"name": "fixture.mp4"},
                resumable=True,
            )
        self.assertEqual(result, {"id": "fixture-file"})
        self.assertEqual(send.call_count, 3)

    def test_slow_upload_stops_before_worker_lease_expires(self):
        client = DriveClient.__new__(DriveClient)
        client.api = Mock()
        client.call = Mock(return_value=(None, None))
        with (
            patch("storage.drive.monotonic", side_effect=[0, 1, 361]),
            self.assertRaisesRegex(DriveError, "^drive_upload_timeout$") as raised,
        ):
            client.upload_blob(BytesIO(b"sample"), "video/mp4", {}, resumable=True)
        self.assertTrue(raised.exception.retryable)
        self.assertEqual(client.call.call_count, 1)

    def test_network_diagnostic_never_logs_exception_content(self):
        client = DriveClient.__new__(DriveClient)
        with (
            self.assertLogs("storage.drive", level="WARNING") as logs,
            self.assertRaisesRegex(DriveError, "^drive_unavailable$"),
        ):
            client.call(Mock(side_effect=TimeoutError("private-token-and-url")))
        self.assertIn("TimeoutError", logs.output[0])
        self.assertNotIn("private-token-and-url", " ".join(logs.output))
