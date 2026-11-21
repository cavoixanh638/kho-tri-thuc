"""Optional actual Chromium navigation acceptance on isolated QA PostgreSQL."""

import json
import os
import subprocess
from pathlib import Path
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import LiveServerTestCase, override_settings

from .models import Item


@skipUnless(
    os.getenv("KT124_BROWSER_NATIVE") == "1",
    "optional native Chromium navigation acceptance",
)
@override_settings(ROOT_URLCONF="catalog.test_navigation")
class NavigationBrowserTests(LiveServerTestCase):
    host = "127.0.0.1"

    def test_actual_api_wiki_outline_and_twenty_palette_actions(self):
        self.assertEqual(str(connection.settings_dict["PORT"]), "62224")
        self.assertIn("kt_124", connection.settings_dict["NAME"])
        owner = get_user_model().objects.create_user(
            username="navigation-browser", password="qa-navigation-only"
        )
        focus = Item.objects.create(
            owner=owner,
            kind="text",
            title="Nghiên cứu",
            note="# H1 Tiếng Việt\r\n\r\n## H2\r\n\r\n### H3\r\n\r\n#### H4\r\n\r\n##### H5\r\n\r\n###### H6\r\n",
        )
        first = Item.objects.create(
            owner=owner, kind="text", title="Trùng tên", note="Bài thứ nhất"
        )
        Item.objects.create(
            owner=owner, kind="text", title="Trùng tên", note="Bài thứ hai"
        )
        # Reverse-chronological navigation puts the second note first. ArrowDown
        # chooses first (created earlier), and the stable UUID is asserted.
        env = {
            **os.environ,
            "KT124_API": self.live_server_url,
            "KT124_CASES": json.dumps(
                {"focus": str(focus.pk), "second": str(first.pk)}
            ),
        }
        web = Path(__file__).resolve().parents[2] / "web"
        result = subprocess.run(
            ["node", "tests/kt124-browser.mjs"],
            cwd=web,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        self.assertEqual(result.returncode, 0, (result.stdout + result.stderr)[-8000:])
        focus.refresh_from_db()
        self.assertIn(f"](#/muc/{first.pk})", focus.note)
        self.assertEqual(Item.objects.count(), 3)
        print(result.stdout)
