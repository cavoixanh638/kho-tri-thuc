"""Atomic optional edit preconditions without changing immutable capture history."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.contrib.auth import get_user_model
from django.db import close_old_connections
from django.test import Client, TransactionTestCase
from ingestion.models import CaptureEvent
from jobs.models import Job

from .models import Item


class NotesUxContractTests(TransactionTestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="contracts-owner")
        self.other = get_user_model().objects.create_user(username="contracts-other")
        self.item = Item.objects.create(
            owner=self.owner, kind="text", note="Gốc Tiếng Việt\r\n"
        )
        self.event = CaptureEvent.objects.create(
            owner=self.owner, item=self.item, raw_kind="text", raw_text=self.item.note
        )
        self.url = f"/api/v1/items/{self.item.pk}"
        self.client.force_login(self.owner)

    def patch(self, body):
        return self.client.patch(self.url, body, content_type="application/json")

    def test_summary_exposes_real_edit_version_and_old_clients_remain_compatible(self):
        self.assertEqual(self.client.get(self.url).json()["user_edit_version"], 0)
        response = self.patch({"note": "Cũ vẫn lưu được"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user_edit_version"], 1)
        self.assertEqual(
            self.client.get("/api/v1/items").json()["results"][0]["user_edit_version"],
            1,
        )

    def test_stale_precondition_does_not_write_fields_version_jobs_or_capture(self):
        captured = self.event.raw_text, self.event.server_received_at
        self.assertEqual(
            self.patch({"note": "Phiên thắng", "expected_edit_version": 0}).status_code,
            200,
        )
        before = Item.objects.values().get(pk=self.item.pk)
        jobs = list(Job.objects.values())
        response = self.patch(
            {
                "note": "Phiên cũ",
                "title": "Ghi đè",
                "favorite": True,
                "expected_edit_version": 0,
            }
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), {"code": "edit_conflict"})
        self.assertEqual(Item.objects.values().get(pk=self.item.pk), before)
        self.assertEqual(list(Job.objects.values()), jobs)
        self.event.refresh_from_db()
        self.assertEqual((self.event.raw_text, self.event.server_received_at), captured)

    def test_precondition_validation_noop_and_nontext_mutations(self):
        for invalid in (-1, True, "0", 0.5):
            with self.subTest(invalid=invalid):
                self.assertEqual(
                    self.patch(
                        {"note": "bad", "expected_edit_version": invalid}
                    ).status_code,
                    422,
                )
        self.assertEqual(
            self.patch({"note": self.item.note, "expected_edit_version": 0}).json()[
                "user_edit_version"
            ],
            0,
        )
        self.assertEqual(
            self.patch({"favorite": True, "expected_edit_version": 0}).json()[
                "user_edit_version"
            ],
            0,
        )
        changed = self.patch(
            {"title": "Tiêu đề", "description": "Mô tả", "expected_edit_version": 0}
        )
        self.assertEqual(changed.json()["user_edit_version"], 1)
        self.item.refresh_from_db()
        self.assertFalse(hasattr(self.item, "expected_edit_version"))

    def test_deleted_after_preflight_blocks_new_versioned_text_write(self):
        self.assertEqual(self.patch({"deleted": True}).status_code, 200)
        rejected = self.patch({"note": "Lưu sau xóa", "expected_edit_version": 0})
        self.assertEqual(rejected.status_code, 409)
        self.item.refresh_from_db()
        self.assertEqual(self.item.note, "Gốc Tiếng Việt\r\n")
        self.assertIsNotNone(self.item.deleted_at)

    def test_precondition_does_not_reveal_another_owners_version(self):
        self.client.force_login(self.other)
        self.assertEqual(
            self.patch({"note": "x", "expected_edit_version": 999}).status_code, 404
        )
        self.client.logout()
        self.assertEqual(
            self.patch({"note": "x", "expected_edit_version": 0}).status_code, 401
        )

    def test_two_concurrent_clients_with_same_version_have_exactly_one_winner(self):
        barrier = Barrier(2)

        def save(note):
            close_old_connections()
            try:
                client = Client()
                client.force_login(self.owner)
                barrier.wait(timeout=10)
                result = client.patch(
                    self.url,
                    {"note": note, "expected_edit_version": 0},
                    content_type="application/json",
                )
                return result.status_code, note
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(
                executor.map(save, ["Phiên A giữ nguyên\r\n", "Phiên B Tiếng Việt\n"])
            )
        self.assertEqual(sorted(status for status, _ in results), [200, 409])
        winner = next(note for status, note in results if status == 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.note.encode(), winner.encode())
        self.assertEqual(self.item.user_edit_version, 1)
        self.assertEqual(Job.objects.count(), 1)
        self.assertEqual(CaptureEvent.objects.count(), 1)
