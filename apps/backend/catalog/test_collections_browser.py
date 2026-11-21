"""Opt-in native Chrome acceptance against actual Django collection endpoints."""

import json
import os
import subprocess
from pathlib import Path
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import LiveServerTestCase, override_settings

from .models import Item, ItemTopic, Topic


@skipUnless(
    os.getenv("KT125_BROWSER_NATIVE") == "1", "Opt-in real Chrome collection workflow"
)
@override_settings(ROOT_URLCONF="catalog.test_collections")
class CollectionBrowserTests(LiveServerTestCase):
    host = "127.0.0.1"

    def test_native_saved_collection_crud_views_and_dynamic_membership(self):
        self.assertEqual(str(connection.settings_dict["PORT"]), "62224")
        self.assertIn("kt_125", connection.settings_dict["NAME"])
        self.assertTrue(os.environ.get("KT125_CDP_HELPER"))
        owner = get_user_model().objects.create_user(
            username="collection-browser", password="synthetic-collections-only"
        )
        topic = Topic.objects.create(owner=owner, name="Nghiên cứu công khai")
        rows = []
        for index in range(5):
            item = Item.objects.create(
                owner=owner,
                kind="text",
                title=f"Tri thức mẫu {index}",
                note=f"# Nội dung tiếng Việt {index}\n\nNguồn và ghi chú.",
                favorite=index < 3,
            )
            ItemTopic.objects.create(item=item, topic=topic, user_pinned=True)
            rows.append(str(item.pk))
        web = Path(__file__).resolve().parents[2] / "web"
        environment = {
            **os.environ,
            "KT125_API": self.live_server_url,
            "KT125_ROWS": json.dumps(rows),
        }
        result = subprocess.run(
            ["node", "tests/kt125-browser.mjs"],
            cwd=web,
            env=environment,
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=180,
            check=False,
        )
        self.assertEqual(result.returncode, 0, (result.stdout + result.stderr)[-8000:])
        print(result.stdout)
