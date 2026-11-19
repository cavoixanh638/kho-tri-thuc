from io import BytesIO
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from .drive import DriveClient, DriveError


class DriveTransportTests(SimpleTestCase):
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
