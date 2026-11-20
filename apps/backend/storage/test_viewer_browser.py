"""Optional real Chrome + actual Django API test, generated media only.

Run with KT116_BROWSER_NATIVE=1, KT116_CDP_HELPER and FFMPEG_BINARY set.
Requires the isolated QA PostgreSQL server on 127.0.0.1:62224; no Drive access.
"""

import array
import hashlib
import io
import json
import os
import subprocess
import tempfile
import wave
from pathlib import Path
from unittest import skipUnless
from unittest.mock import patch

from catalog.models import Item
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import LiveServerTestCase
from django.utils import timezone

from .models import Asset, StorageLocation


@skipUnless(
    os.getenv("KT116_BROWSER_NATIVE") == "1", "optional native Chrome viewer acceptance"
)
class ViewerNativeBrowserTests(LiveServerTestCase):
    host = "127.0.0.1"

    def test_private_django_bytes_decode_and_seek_both_codecs(self):
        self.assertEqual(str(connection.settings_dict["PORT"]), "62224")
        self.assertIn("kt_ux_viewer", connection.settings_dict["NAME"])
        self.assertTrue(
            os.getenv("KT116_CDP_HELPER"), "explicit external CDP helper required"
        )
        owner = get_user_model().objects.create_user(
            username="kt-viewer-synthetic", password="qa-viewer-only"
        )
        samples = array.array("h", [0, 1000, 0, -1000] * (48_000 * 30 // 4 * 2))
        wav = io.BytesIO()
        with wave.open(wav, "wb") as sink:
            sink.setnchannels(2)
            sink.setsampwidth(2)
            sink.setframerate(48_000)
            sink.writeframes(samples.tobytes())
        with tempfile.TemporaryDirectory(prefix="kt-viewer-generated-") as directory:
            video = Path(directory) / "source.webm"
            subprocess.run(
                [
                    settings.FFMPEG_BINARY,
                    "-nostdin",
                    "-loglevel",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc=size=320x180:rate=10",
                    "-t",
                    "22",
                    "-c:v",
                    "libvpx",
                    "-b:v",
                    "300k",
                    "-deadline",
                    "realtime",
                    "-pix_fmt",
                    "yuv420p",
                    str(video),
                ],
                check=True,
                timeout=60,
                capture_output=True,
            )
            bodies, cases, reads = {}, [], []
            for mime, body in (
                ("audio/wav", wav.getvalue()),
                ("video/webm", video.read_bytes()),
            ):
                item = Item.objects.create(owner=owner, kind="file")
                asset = Asset.objects.create(
                    item=item,
                    mime=mime,
                    size=len(body),
                    sha256=hashlib.sha256(body).hexdigest(),
                    original_filename="synthetic-source",
                    content_version=1,
                )
                StorageLocation.objects.create(
                    asset=asset,
                    provider_file_id=str(asset.pk),
                    status="verified",
                    provider_revision="1",
                    verified_at=timezone.now(),
                )
                bodies[str(asset.pk)] = body
                cases.append(
                    {
                        "assetId": str(asset.pk),
                        "version": asset.sha256,
                        "mime": mime,
                        "size": len(body),
                    }
                )

            class SyntheticStorage:
                def read_range(self, asset, start, end):
                    reads.append({"asset": str(asset.pk), "start": start, "end": end})
                    return bodies[str(asset.pk)][start : end + 1]

            env = {
                **os.environ,
                "KT116_API": self.live_server_url,
                "KT116_CASES": json.dumps(cases),
            }
            web = Path(__file__).resolve().parents[2] / "web"
            with patch(
                "storage.viewer_api.storage_for_owner", return_value=SyntheticStorage()
            ):
                result = subprocess.run(
                    ["node", "tests/kt116-private-browser.mjs"],
                    check=False,
                    cwd=web,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=160,
                )
            self.assertEqual(
                result.returncode, 0, (result.stdout + result.stderr)[-8000:]
            )
            self.assertTrue(
                any(row["end"] - row["start"] + 1 == 4 * 1024 * 1024 for row in reads),
                "large open-ended range used capped slice",
            )
            self.assertTrue(
                all(row["end"] - row["start"] + 1 <= 4 * 1024 * 1024 for row in reads)
            )
            print(result.stdout)
