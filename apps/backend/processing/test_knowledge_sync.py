import hashlib
from datetime import timedelta
from unittest.mock import patch

from catalog.models import Item
from django.contrib.auth import get_user_model
from django.test import Client, TransactionTestCase
from django.utils import timezone
from jobs.handlers import JobFailure
from jobs.models import Job
from jobs.repository import JobRepository
from jobs.worker import Worker
from storage.drive import FOLDER_MIME, DriveError
from storage.models import DriveAccount, KnowledgeExport

from .knowledge_api import status
from .knowledge_sync import configure, export_knowledge, request_sync


class Request:
    def __init__(self, run):
        self.run = run

    def execute(self):
        return self.run()


class FakeDrive:
    def __init__(self):
        self.api = self
        self.rows, self.payloads = {}, {}
        self.counter = self.creates = self.updates = 0
        self.lose_response = False
        self.on_upload = None

    def files(self):
        return self

    def execute(self, request):
        return request.execute()

    def reserve_file_id(self):
        self.counter += 1
        return f"reserved-{self.counter}"

    def get_file(self, file_id, fields):
        if file_id not in self.rows:
            raise DriveError("drive_not_found", status=404)
        return dict(self.rows[file_id])

    def list(self, **kwargs):
        return Request(
            lambda: {
                "files": [
                    {"id": key}
                    for key, row in self.rows.items()
                    if row.get("mimeType") == FOLDER_MIME
                ]
            }
        )

    def create(self, *, body, fields):
        def run():
            if body["id"] in self.rows:
                raise DriveError("drive_request_failed", status=409)
            self.rows[body["id"]] = dict(body)
            return dict(body)

        return Request(run)

    def put(self, file_id, body, mime):
        self.payloads[file_id] = body
        self.rows[file_id].update(
            size=str(len(body)),
            mimeType=mime,
            sha256Checksum=hashlib.sha256(body).hexdigest(),
        )

    def upload_blob(self, stream, mime, metadata, *, resumable):
        if metadata["id"] in self.rows:
            raise DriveError("drive_request_failed", status=409)
        self.rows[metadata["id"]] = dict(metadata)
        self.put(metadata["id"], stream.read(), mime)
        self.creates += 1
        if self.on_upload:
            self.on_upload()
            self.on_upload = None
        if self.lose_response:
            self.lose_response = False
            raise DriveError("drive_unavailable", retryable=True)
        return {"id": metadata["id"]}

    def update(self, *, fileId, body, fields, media_body=None):
        def run():
            self.rows[fileId].update(body)
            if media_body is not None:
                self.put(
                    fileId, media_body.getbytes(0, media_body.size()), body["mimeType"]
                )
            self.updates += 1
            return {"id": fileId}

        return Request(run)


class KnowledgeSyncTests(TransactionTestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="export-owner")
        self.other = get_user_model().objects.create_user(username="export-other")
        self.item = Item.objects.create(
            owner=self.owner, kind="text", note="Ghi chú nguyên văn"
        )
        self.account = DriveAccount.objects.create(
            owner=self.owner,
            google_user_id="fixture",
            root_folder_id="fixture-root",
            state="connected",
        )
        self.drive = FakeDrive()
        self.patch = patch(
            "processing.knowledge_sync.client_for_owner",
            return_value=(self.drive, self.account),
        )
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.worker = Worker({"export_knowledge": export_knowledge})

    def enable(self):
        configure(self.item, enabled=True, format="markdown")

    def record(self):
        return KnowledgeExport.objects.get(item=self.item)

    def test_lost_upload_response_retries_same_persisted_id_and_verifies_bytes(self):
        self.enable()
        self.drive.lose_response = True
        self.assertTrue(self.worker.run_once())
        first = self.record()
        self.assertEqual(first.status, "failed")
        self.assertTrue(first.provider_file_id)
        self.assertEqual(self.drive.creates, 1)
        self.account.refresh_from_db()
        self.assertTrue(self.account.knowledge_folder_id)
        Job.objects.filter(state="retry").update(retry_at=timezone.now())
        self.assertTrue(self.worker.run_once())
        final = self.record()
        self.assertEqual(final.provider_file_id, first.provider_file_id)
        self.assertEqual(final.status, "synced")
        self.assertEqual(self.drive.creates, 1)
        self.assertIn(
            self.item.note, self.drive.payloads[final.provider_file_id].decode()
        )
        request_sync(self.item.pk, force=True)
        self.worker.run_once()
        self.assertEqual(self.drive.creates, 1)
        self.assertEqual(self.drive.updates, 0)

    def test_edit_updates_same_file_and_get_detects_bulk_update_as_stale(self):
        self.enable()
        self.worker.run_once()
        first = self.record()
        Item.objects.filter(pk=self.item.pk).update(note="Nội dung mới")
        self.assertTrue(status(self.item)["stale"])
        request_sync(self.item.pk, force=True)
        self.worker.run_once()
        second = self.record()
        self.assertEqual(second.provider_file_id, first.provider_file_id)
        self.assertNotEqual(second.exported_version, first.exported_version)
        self.assertIn(
            "Nội dung mới", self.drive.payloads[second.provider_file_id].decode()
        )
        self.assertEqual(self.drive.creates, 1)

    def test_signal_change_and_change_during_upload_eventually_export_latest(self):
        self.enable()
        self.drive.on_upload = lambda: Item.objects.filter(pk=self.item.pk).update(
            note="Sửa trong lúc upload"
        )
        self.worker.run_once()
        self.assertEqual(self.record().status, "pending")
        self.worker.run_once()
        self.assertEqual(self.record().status, "synced")
        self.item.refresh_from_db()
        self.item.note = "Chỉnh sửa qua save"
        self.item.save(update_fields=["note"])
        self.assertTrue(
            Job.objects.filter(kind="export_knowledge", state="queued").exists()
        )
        self.worker.run_once()
        self.assertIn(
            self.item.note, self.drive.payloads[self.record().provider_file_id].decode()
        )

    def test_delete_restore_and_opt_out_only_trash_managed_derivative(self):
        self.enable()
        self.worker.run_once()
        file_id = self.record().provider_file_id
        self.drive.rows["original"] = {
            "id": "original",
            "appProperties": {"kt_asset_id": "original"},
        }
        self.item.deleted_at = timezone.now()
        self.item.save(update_fields=["deleted_at"])
        self.worker.run_once()
        self.assertTrue(self.drive.rows[file_id]["trashed"])
        self.item.deleted_at = None
        self.item.save(update_fields=["deleted_at"])
        self.worker.run_once()
        self.assertFalse(self.drive.rows[file_id]["trashed"])
        configure(self.item, enabled=False, format="markdown")
        self.worker.run_once()
        self.assertEqual(self.record().status, "disabled")
        self.assertTrue(self.drive.rows[file_id]["trashed"])
        self.assertNotIn("trashed", self.drive.rows["original"])
        self.assertEqual(self.drive.creates, 1)

    def test_expired_lease_cannot_upload_and_identity_mismatch_cannot_overwrite(self):
        self.enable()
        job = JobRepository.claim(["export_knowledge"])
        Job.objects.filter(pk=job.pk).update(
            lease_until=timezone.now() - timedelta(seconds=1)
        )
        with self.assertRaises(JobFailure):
            export_knowledge(job)
        self.assertEqual(self.drive.creates, 0)
        self.assertFalse(self.record().provider_file_id)
        Job.objects.filter(pk=job.pk).update(state="retry", retry_at=timezone.now())
        self.worker.run_once()
        file_id = self.record().provider_file_id
        self.drive.rows[file_id]["appProperties"] = {
            "kt_item_id": "somebody-else",
            "kt_knowledge": "1",
        }
        old = self.drive.payloads[file_id]
        self.item.note = "Không được ghi đè"
        self.item.save(update_fields=["note"])
        self.worker.run_once()
        self.assertEqual(self.record().last_error, "knowledge_identity_mismatch")
        self.assertEqual(self.drive.payloads[file_id], old)

    def test_no_automatic_opt_in_and_sensitive_input_is_not_sent(self):
        self.item.note = "Unexported text"
        self.item.save(update_fields=["note"])
        self.assertFalse(KnowledgeExport.objects.exists())
        self.assertFalse(self.worker.run_once())
        self.item.note = "client_secret=" + "fixture" * 8
        self.item.save(update_fields=["note"])
        self.enable()
        self.worker.run_once()
        self.assertEqual(self.record().last_error, "knowledge_sensitive_input")
        self.assertFalse(self.drive.payloads)

    def test_owner_scope_csrf_format_validation_and_ten_item_pilot_limit(self):
        url = f"/api/v1/items/{self.item.pk}/knowledge-export"
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(url).json()["enabled"], False)
        self.assertEqual(
            self.client.post(
                url,
                data={"enabled": True, "format": "docs"},
                content_type="application/json",
            ).status_code,
            422,
        )
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(self.owner)
        self.assertEqual(
            csrf.post(
                url,
                data={"enabled": True, "format": "text"},
                content_type="application/json",
            ).status_code,
            403,
        )
        for number in range(10):
            item = Item.objects.create(
                owner=self.owner, kind="text", note=f"Pilot {number}"
            )
            configure(item, enabled=True, format="text")
        reply = self.client.post(
            url,
            data={"enabled": True, "format": "text"},
            content_type="application/json",
        )
        self.assertEqual(reply.status_code, 409)
        self.assertEqual(reply.json()["error"], "knowledge_pilot_limit")
        self.assertFalse(KnowledgeExport.objects.filter(item=self.item).exists())
