import json
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from catalog.models import Item, Source
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TransactionTestCase, override_settings
from django.utils import timezone
from ingestion.models import CaptureEvent
from jobs.handlers import JobFailure
from jobs.models import Job
from jobs.repository import JobRepository
from jobs.worker import Worker
from storage.models import Asset, StorageLocation
from storage.upload_job import staging_path, upload_asset

from .source_fetch import SourceProvenance, SourceResult, SourceStatus
from .source_jobs import fetch_source_job
from .video_download import VideoDownloadError
from .video_jobs import VIDEO_KIND, download_video, probe_video

URL = "https://www.facebook.com/reel/123456789012345"
MEDIA = {"duration": 2.5, "width": 320, "height": 240, "audio": True}
PAYLOAD = b"test-video-original-bytes"


class VideoProbeTests(SimpleTestCase):
    @override_settings(FFPROBE_BINARY="probe-binary")
    def test_probe_checks_local_mp4_with_video_and_audio(self):
        video = {
            "streams": [{"codec_type": "video", "width": 320, "height": 240}],
            "format": {"duration": "2.5", "format_name": "mov,mp4,m4a,3gp,3g2,mj2"},
        }
        audio = {"streams": [{"codec_type": "audio"}]}
        responses = [
            SimpleNamespace(returncode=0, stdout=json.dumps(x).encode())
            for x in (video, audio)
        ]
        with patch(
            "processing.video_jobs.subprocess.run", side_effect=responses
        ) as run:
            self.assertEqual(probe_video(Path("sample.mp4")), MEDIA)
        for call in run.call_args_list:
            command = call.args[0]
            self.assertEqual(command[0], "probe-binary")
            self.assertEqual(command[command.index("-protocol_whitelist") + 1], "file")
            self.assertEqual(command[command.index("-format_whitelist") + 1], "mov")
            self.assertEqual(call.kwargs["timeout"], 15)
            self.assertNotIn("DJANGO_SECRET_KEY", call.kwargs["env"])
            self.assertNotIn("GOOGLE_DRIVE_CLIENT_SECRET", call.kwargs["env"])

    def test_probe_missing_audio_or_invalid_json_is_rejected(self):
        outputs = [
            {
                "streams": [{"codec_type": "video", "width": 320, "height": 240}],
                "format": {"duration": "2.5", "format_name": "mp4"},
            },
            {"streams": []},
        ]
        with (
            patch(
                "processing.video_jobs.subprocess.run",
                side_effect=[
                    SimpleNamespace(returncode=0, stdout=json.dumps(value).encode())
                    for value in outputs
                ],
            ),
            self.assertRaisesRegex(JobFailure, "video_invalid_media"),
        ):
            probe_video(Path("sample.mp4"))
        with (
            patch(
                "processing.video_jobs.subprocess.run",
                return_value=SimpleNamespace(returncode=0, stdout=b"invalid"),
            ),
            self.assertRaisesRegex(JobFailure, "video_probe_failed"),
        ):
            probe_video(Path("sample.mp4"))


class VideoJobTests(TransactionTestCase):
    def setUp(self):
        self.scratch = TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.settings = override_settings(UPLOAD_STAGING_ROOT=self.scratch.name)
        self.settings.enable()
        self.addCleanup(self.settings.disable)
        self.owner = get_user_model().objects.create_user(username="video-owner")
        self.item = Item.objects.create(
            owner=self.owner, kind=Item.Kind.LINK, note="Ghi chú giữ nguyên"
        )
        self.capture = CaptureEvent.objects.create(
            owner=self.owner,
            item=self.item,
            raw_kind=CaptureEvent.Kind.LINK,
            original_url=URL,
            raw_text="Dữ liệu gửi nguyên văn",
        )
        self.source = Source.objects.create(
            item=self.item,
            original_url=URL,
            canonical_url=URL,
            identity_hash="video-fixture",
        )
        self.worker = Worker({VIDEO_KIND: download_video})

    def enqueue(self, key="video-fixture", **overrides):
        return JobRepository.enqueue(
            kind=VIDEO_KIND,
            idempotency_key=key,
            item=self.item,
            input_ref={
                "source_id": self.source.pk,
                "capture_id": str(self.capture.pk),
                **overrides,
            },
        )

    def download(self, url, path):
        self.assertEqual(url, URL)
        path.write_bytes(PAYLOAD)
        return SimpleNamespace(
            path=path,
            title="External title",
            description="External description",
            platform_id="123456789012345",
            duration=2.5,
        )

    def run_download(self, **kwargs):
        with (
            patch(
                "processing.video_download.download_facebook", side_effect=self.download
            ) as mocked,
            patch("processing.video_jobs.probe_video", return_value=MEDIA),
        ):
            self.assertTrue(self.worker.run_once())
        return mocked

    def test_download_stages_one_asset_and_upload_job_without_rewriting_capture(self):
        stamp, received = self.item.saved_at, self.capture.server_received_at
        job = self.enqueue()
        self.run_download()
        asset = Asset.objects.get(item=self.item)
        self.assertEqual(staging_path(asset.pk).read_bytes(), PAYLOAD)
        self.assertEqual(asset.mime, "video/mp4")
        self.assertEqual(asset.size, len(PAYLOAD))
        self.assertEqual(
            Job.objects.filter(kind="upload_asset", item=self.item).count(), 1
        )
        self.source.refresh_from_db()
        self.assertEqual(self.source.metadata["video"]["asset_id"], str(asset.pk))
        self.assertEqual(self.source.metadata["video"]["audio"], True)
        self.assertEqual(self.source.platform, "facebook")
        self.item.refresh_from_db()
        job.refresh_from_db()
        self.capture.refresh_from_db()
        self.assertEqual(job.state, Job.State.DONE)
        self.assertEqual(self.item.source_fetch, "done")
        self.assertEqual(self.item.asset_storage, "pending")
        self.assertEqual(self.item.note, "Ghi chú giữ nguyên")
        self.assertEqual(self.item.saved_at, stamp)
        self.assertEqual(self.capture.server_received_at, received)
        self.assertEqual(self.capture.raw_text, "Dữ liệu gửi nguyên văn")
        self.assertEqual(CaptureEvent.objects.filter(item=self.item).count(), 1)

    def test_retry_uses_durable_staging_and_same_asset(self):
        job = self.enqueue()
        self.run_download()
        asset = Asset.objects.get(item=self.item)
        Job.objects.filter(pk=job.pk).update(state=Job.State.RETRY, attempt=0)
        with (
            patch("processing.video_download.download_facebook") as download,
            patch("processing.video_jobs.probe_video", return_value=MEDIA),
        ):
            self.assertTrue(self.worker.run_once())
            download.assert_not_called()
        self.assertEqual(Asset.objects.get(item=self.item).pk, asset.pk)
        self.assertEqual(
            Job.objects.filter(kind="upload_asset", item=self.item).count(), 1
        )

    def test_verified_asset_retry_skips_network_and_probe(self):
        job = self.enqueue()
        self.run_download()
        asset = Asset.objects.get(item=self.item)
        StorageLocation.objects.create(
            asset=asset,
            provider_file_id="mock-file",
            status="verified",
            verified_at=timezone.now(),
        )
        staging_path(asset.pk).unlink()
        Job.objects.filter(pk=job.pk).update(state=Job.State.RETRY, attempt=0)
        with (
            patch("processing.video_download.download_facebook") as download,
            patch("processing.video_jobs.probe_video") as probe,
        ):
            self.assertTrue(self.worker.run_once())
            download.assert_not_called()
            probe.assert_not_called()
        self.item.refresh_from_db()
        self.assertEqual(self.item.asset_storage, "verified")
        self.assertEqual(Asset.objects.count(), 1)

    def test_lost_lease_cannot_publish_asset_or_staging(self):
        self.enqueue()

        def revoked(url, path):
            result = self.download(url, path)
            Job.objects.filter(kind=VIDEO_KIND).update(
                lease_until=timezone.now() - timedelta(seconds=1)
            )
            return result

        with (
            patch("processing.video_download.download_facebook", side_effect=revoked),
            patch("processing.video_jobs.probe_video", return_value=MEDIA),
        ):
            self.assertTrue(self.worker.run_once())
        self.assertFalse(Asset.objects.exists())
        self.assertFalse(Job.objects.filter(kind="upload_asset").exists())
        self.assertEqual(list(Path(self.scratch.name).iterdir()), [])

    def test_capture_from_another_owner_is_rejected_before_network(self):
        stranger = get_user_model().objects.create_user(username="other-owner")
        other = Item.objects.create(owner=stranger, kind=Item.Kind.LINK)
        capture = CaptureEvent.objects.create(
            owner=stranger,
            item=other,
            raw_kind=CaptureEvent.Kind.LINK,
            original_url=URL,
        )
        job = self.enqueue(capture_id=str(capture.pk))
        with patch("processing.video_download.download_facebook") as download:
            self.assertTrue(self.worker.run_once())
            download.assert_not_called()
        job.refresh_from_db()
        self.assertEqual(job.error_code, "invalid_video_job")

    def test_failed_download_keeps_source_and_safe_error_without_asset(self):
        job = self.enqueue()
        with patch(
            "processing.video_download.download_facebook",
            side_effect=VideoDownloadError("video_unavailable", retryable=False),
        ):
            self.assertTrue(self.worker.run_once())
        job.refresh_from_db()
        self.source.refresh_from_db()
        self.assertEqual(job.state, Job.State.FAILED)
        self.assertEqual(self.source.original_url, URL)
        self.assertEqual(
            self.source.metadata["video"]["error_code"], "video_unavailable"
        )
        self.assertFalse(Asset.objects.exists())

    def test_user_edit_is_not_replaced_by_downloader(self):
        Item.objects.filter(pk=self.item.pk).update(
            title="Curated", description="", user_edit_version=1
        )
        self.enqueue()
        self.run_download()
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, "Curated")
        self.assertEqual(self.item.description, "")

    def test_download_is_queued_even_when_html_is_access_denied(self):
        JobRepository.enqueue(
            kind="fetch_source",
            idempotency_key="html",
            item=self.item,
            input_ref={"source_id": self.source.pk, "capture_id": str(self.capture.pk)},
        )
        denied = SourceResult(
            SourceStatus.ACCESS_DENIED,
            SourceProvenance(URL, timezone.now(), http_status=403),
            error_code="http_access_denied",
        )
        with patch("processing.source_jobs.fetch_source", return_value=denied):
            self.assertTrue(Worker({"fetch_source": fetch_source_job}).run_once())
        self.assertEqual(Job.objects.filter(kind=VIDEO_KIND, item=self.item).count(), 1)
        self.item.refresh_from_db()
        self.assertEqual(self.item.source_fetch, "pending")

    def test_html_refresh_cannot_downgrade_verified_video(self):
        self.enqueue()
        self.run_download()
        asset = Asset.objects.get(item=self.item)
        StorageLocation.objects.create(
            asset=asset,
            provider_file_id="mock-file",
            status="verified",
            verified_at=timezone.now(),
        )
        JobRepository.enqueue(
            kind="fetch_source",
            idempotency_key="html",
            item=self.item,
            input_ref={"source_id": self.source.pk, "capture_id": str(self.capture.pk)},
        )
        denied = SourceResult(
            SourceStatus.ACCESS_DENIED,
            SourceProvenance(URL, timezone.now(), http_status=403),
            error_code="http_access_denied",
        )
        with patch("processing.source_jobs.fetch_source", return_value=denied):
            self.assertTrue(Worker({"fetch_source": fetch_source_job}).run_once())
        self.item.refresh_from_db()
        self.assertEqual(self.item.source_fetch, "done")
        self.assertEqual(self.item.asset_storage, "verified")

    def test_retry_endpoint_includes_video_and_keeps_capture_count(self):
        job = self.enqueue()
        Job.objects.filter(pk=job.pk).update(state=Job.State.FAILED, attempt=5)
        self.client.force_login(self.owner)
        response = self.client.post(f"/api/v1/items/{self.item.pk}/retry")
        self.assertEqual(response.json(), {"queued": 1})
        job.refresh_from_db()
        self.assertEqual(job.state, Job.State.RETRY)
        self.assertEqual(job.attempt, 0)
        self.assertEqual(CaptureEvent.objects.filter(item=self.item).count(), 1)
        self.run_download()
        job.refresh_from_db()
        self.assertEqual(job.state, Job.State.DONE)

    def test_upload_completion_preserves_link_source_state(self):
        self.enqueue()
        self.run_download()
        asset = Asset.objects.get(item=self.item)

        def save(original, stream):
            self.assertEqual(stream.read(), PAYLOAD)
            return StorageLocation.objects.create(
                asset=original,
                provider_file_id="mock-file",
                status="verified",
                verified_at=timezone.now(),
            )

        with (
            patch("storage.upload_job.storage_for_owner") as factory,
            patch("storage.upload_job.extract_from_staging"),
            patch("storage.upload_job.thumbnail_from_staging"),
        ):
            factory.return_value.save.side_effect = save
            self.assertTrue(Worker({"upload_asset": upload_asset}).run_once())
        self.item.refresh_from_db()
        self.assertEqual(self.item.source_fetch, "done")
        self.assertEqual(self.item.asset_storage, "verified")
        self.assertFalse(staging_path(asset.pk).exists())

    def test_database_rollback_after_stage_publication_reuses_same_path(self):
        job = self.enqueue()
        with (
            patch(
                "processing.video_download.download_facebook", side_effect=self.download
            ),
            patch("processing.video_jobs.probe_video", return_value=MEDIA),
            patch(
                "processing.video_jobs._upload_job",
                side_effect=RuntimeError("commit failed"),
            ),
        ):
            self.assertTrue(self.worker.run_once())
        self.assertFalse(Asset.objects.exists())
        before = list(Path(self.scratch.name).iterdir())
        self.assertEqual(len(before), 1)
        Job.objects.filter(pk=job.pk).update(retry_at=timezone.now())
        self.run_download()
        asset = Asset.objects.get(item=self.item)
        self.assertEqual(staging_path(asset.pk), before[0])
        self.assertEqual(list(Path(self.scratch.name).iterdir()), before)
        self.assertEqual(Job.objects.filter(kind="upload_asset").count(), 1)
