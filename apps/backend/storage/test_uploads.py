from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connections
from django.http import HttpRequest
from django.middleware.csrf import get_token
from django.test import Client, TransactionTestCase, override_settings
from django.urls import path
from django.utils import timezone
from ninja import NinjaAPI

from catalog.models import Item
from jobs.models import Job
from jobs.worker import Worker

from . import uploads
from .models import Asset, StorageLocation
from .service import DriveStorage
from .test_drive_storage import FakeDrive
from .upload_job import UPLOAD_KIND, staging_path, upload_asset

api = NinjaAPI(urls_namespace="test_upload_api")
api.add_router("/uploads", uploads.router)
urlpatterns = [path("api/v1/", api.urls)]

ENDPOINT = "/api/v1/uploads"
DATA = b"generated file content"


@override_settings(ROOT_URLCONF=__name__)
class UploadTests(TransactionTestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="upload-owner")
        self.client.force_login(self.owner)
        stage = self.enterContext(TemporaryDirectory())
        self.enterContext(override_settings(UPLOAD_STAGING_ROOT=stage))
        self.stage = Path(stage).resolve()

    def post_upload(self, key=None, *, client=None):
        headers = {"HTTP_IDEMPOTENCY_KEY": key} if key is not None else {}
        return (client or self.client).post(
            ENDPOINT,
            {"file": SimpleUploadedFile("sample.txt", DATA, content_type="text/plain")},
            **headers,
        )

    def test_upload_requires_authenticated_session_and_csrf(self):
        anonymous = self.post_upload(client=Client())
        self.assertEqual(anonymous.status_code, 401)
        guarded = Client(enforce_csrf_checks=True)
        guarded.force_login(self.owner)
        rejected = self.post_upload(client=guarded)
        self.assertEqual(rejected.status_code, 403)
        request = HttpRequest()
        header = get_token(request)
        guarded.cookies["csrftoken"] = request.META["CSRF_COOKIE"]
        response = guarded.post(
            ENDPOINT,
            {"file": SimpleUploadedFile("sample.txt", DATA, content_type="text/plain")},
            HTTP_X_CSRFTOKEN=header,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Item.objects.count(), 1)

    def test_receipt_is_durable_and_replay_returns_the_first_upload(self):
        accepted = self.post_upload("stable-key")
        self.assertEqual(accepted.status_code, 201, accepted.content)
        receipt = accepted.json()
        self.assertEqual(receipt["state"], "queued")
        replay = self.post_upload("stable-key")
        self.assertEqual(replay.status_code, 200, replay.content)
        self.assertEqual(replay.json(), receipt)

        item = Item.objects.get(pk=receipt["item_id"], owner=self.owner)
        self.assertEqual(item.kind, Item.Kind.FILE)
        asset = Asset.objects.get(pk=receipt["asset_id"], item=item)
        self.assertEqual(asset.sha256, sha256(DATA).hexdigest())
        self.assertEqual(asset.size, len(DATA))
        job = Job.objects.get(item=item, kind=UPLOAD_KIND)
        self.assertEqual(job.input_ref, {"asset_id": str(asset.pk)})
        self.assertEqual(list(self.stage.iterdir()), [staging_path(asset.pk)])
        self.assertEqual(staging_path(asset.pk).read_bytes(), DATA)

    def test_replay_keys_are_scoped_to_the_owner_and_optional(self):
        first = self.post_upload("key")
        other = Client()
        other.force_login(get_user_model().objects.create_user(username="other"))
        second = self.post_upload("key", client=other)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertNotEqual(first.json()["asset_id"], second.json()["asset_id"])
        self.assertEqual(self.post_upload().status_code, 201)
        self.assertEqual(self.post_upload().status_code, 201)
        self.assertEqual(Item.objects.count(), 4)

    def test_invalid_key_and_oversize_upload_leave_no_rows_or_stage(self):
        invalid = self.post_upload("spaces are invalid")
        self.assertEqual(invalid.status_code, 400)
        with patch.object(uploads, "MAX_UPLOAD_BYTES", 4):
            large = self.post_upload()
            self.assertEqual(large.status_code, 413)
            misdeclared = SimpleUploadedFile("oversize.txt", DATA)
            misdeclared.size = 4
            with self.assertRaises(uploads.UploadTooLarge):
                uploads.accept_upload(self.owner, misdeclared)
        self.assertEqual(list(self.stage.iterdir()), [])
        self.assertFalse(Item.objects.exists())
        self.assertFalse(Asset.objects.exists())
        self.assertFalse(Job.objects.exists())

    def test_concurrent_replay_creates_one_job_and_one_staged_file(self):
        barrier = Barrier(2, timeout=5)
        real_stage = uploads._stage

        def synchronize_stage(*args):
            staged = real_stage(*args)
            barrier.wait()
            return staged

        def post_in_thread():
            try:
                client = Client()
                client.force_login(self.owner)
                return self.post_upload("one-receipt", client=client).status_code
            finally:
                connections.close_all()

        with patch.object(uploads, "_stage", side_effect=synchronize_stage):
            with ThreadPoolExecutor(max_workers=2) as executor:
                statuses = list(executor.map(lambda _: post_in_thread(), range(2)))
        self.assertEqual(sorted(statuses), [200, 201])
        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(Asset.objects.count(), 1)
        self.assertEqual(Job.objects.count(), 1)
        self.assertEqual(len(list(self.stage.iterdir())), 1)

    def test_lost_drive_response_preserves_stage_then_reuses_file_and_cleans_up(self):
        response = self.post_upload()
        self.assertEqual(response.status_code, 201, response.content)
        asset_id = UUID(response.json()["asset_id"])
        job = Job.objects.get()
        staged = staging_path(asset_id)
        fake = FakeDrive()
        fake.lose_upload_response = True
        storage = DriveStorage(
            fake, SimpleNamespace(owner_id=self.owner.pk, root_folder_id="root")
        )
        with patch("storage.upload_job.storage_for_owner", return_value=storage):
            self.assertTrue(Worker({UPLOAD_KIND: upload_asset}).run_once())
            job.refresh_from_db()
            self.assertEqual(job.state, Job.State.RETRY)
            self.assertEqual(staged.read_bytes(), DATA)
            Job.objects.filter(pk=job.pk).update(retry_at=timezone.now())
            self.assertTrue(Worker({UPLOAD_KIND: upload_asset}).run_once())
        self.assertEqual(fake.uploads, 1)
        self.assertEqual(fake.reservations, 1)
        self.assertEqual(
            Asset.objects.get(pk=asset_id).locations.get().status,
            StorageLocation.Status.VERIFIED,
        )
        self.assertFalse(staged.exists())
        job.refresh_from_db()
        self.assertEqual(job.state, Job.State.DONE)
        with patch("storage.upload_job.storage_for_owner") as lookup:
            upload_asset(job)
            lookup.assert_not_called()
