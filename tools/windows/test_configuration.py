import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


@unittest.skipUnless(os.name == "nt", "Windows launcher")
class WindowsConfigurationTests(unittest.TestCase):
    def test_client_is_saved_only_after_matching_redirect_and_without_printing_secrets(
        self,
    ):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec = importlib.util.spec_from_file_location(
                "kt_launch", Path(__file__).with_name("launch.py")
            )
            launcher = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(launcher)
            config = root / "config.json"
            redirect = "http://127.0.0.1:8009/api/v1/integrations/drive/callback"
            config.write_text(
                json.dumps({"environment": {"GOOGLE_DRIVE_REDIRECT_URI": redirect}})
            )
            client = root / "client.json"
            data = {
                "web": {
                    "client_id": "test.apps.googleusercontent.com",
                    "client_secret": "unit-test-secret",
                    "redirect_uris": ["http://wrong.example.invalid"],
                }
            }
            client.write_text(json.dumps(data))
            before = config.read_bytes()
            with patch.object(launcher, "CONFIG", config):
                with self.assertRaises(ValueError):
                    launcher.configure_drive(client)
                self.assertEqual(config.read_bytes(), before)
                data["web"]["redirect_uris"] = [redirect]
                client.write_text(json.dumps(data))
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    launcher.configure_drive(client)
                saved = json.loads(config.read_text())
                self.assertEqual(
                    saved["environment"]["GOOGLE_DRIVE_CLIENT_SECRET"],
                    "unit-test-secret",
                )
                self.assertNotIn("unit-test-secret", output.getvalue())


if __name__ == "__main__":
    unittest.main()
