import hashlib
import json
import os
import sys
import tempfile
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from catalog.models import Item
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from ingestion.models import CaptureEvent
from jobs.handlers import JobFailure
from jobs.models import Job
from jobs.repository import JobRepository
from storage.models import Asset, StorageLocation

from .models import DerivedContent
from .transcribe import child_environment, run, transcribe_file
from .transcript_job import (
    PROCESSOR_VERSION,
    _validate,
    enqueue_transcript,
    transcribe_media,
)


class TranscriptBoundaryTests(SimpleTestCase):
    def test_child_environment_removes_credentials_and_is_offline(self):
        with patch.dict(
            os.environ,
            {
                "GOOGLE_DRIVE_CLIENT_SECRET": "private",
                "HF_TOKEN": "private",
                "POSTGRES_PASSWORD": "private",
            },
        ):
            env = child_environment()
        self.assertNotIn("GOOGLE_DRIVE_CLIENT_SECRET", env)
        self.assertNotIn("HF_TOKEN", env)
        self.assertNotIn("POSTGRES_PASSWORD", env)
        self.assertEqual(env["HF_HUB_OFFLINE"], "1")

    def test_rejects_nonfinite_backwards_oversized_and_inconsistent_output(self):
        good = {
            "state": "done",
            "segments": [{"start": 0.0, "end": 2.0, "text": "Tiếng Việt"}],
        }
        self.assertEqual(len(_validate(good)), 1)
        bad = [
            None,
            {"state": "done", "segments": []},
            {"state": "not_available", "segments": good["segments"]},
        ]
        for changes in (
            {"start": float("nan")},
            {"start": -1},
            {"end": 601.1},
            {"end": -1},
            {"text": "\x00"},
            {"text": "x" * 100001},
            {"text": "\ud800"},
        ):
            bad.append(
                {"state": "done", "segments": [{**good["segments"][0], **changes}]}
            )
        for value in bad:
            with (
                self.subTest(value_type=type(value).__name__),
                self.assertRaises(JobFailure),
            ):
                _validate(value)

    def test_missing_model_is_safe_and_malformed_child_result_is_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory)
            self.assertEqual(
                transcribe_file(model / "media", model)["error"],
                "transcript_model_missing",
            )
            (model / "model.bin").write_bytes(b"model")
            (model / "kt-model.json").write_text("{}")

            def fake_child(*args, **kwargs):
                kwargs["stdout"].write(b"[]")
                kwargs["stdout"].flush()
                return SimpleNamespace(
                    poll=lambda: 0, returncode=0, wait=lambda timeout: None
                )

            with patch(
                "processing.transcribe.subprocess.Popen", side_effect=fake_child
            ):
                self.assertEqual(
                    transcribe_file(model / "media", model)["error"],
                    "transcript_processing_failed",
                )

    def test_inference_verifies_model_and_uses_local_files_only(self):
        with tempfile.TemporaryDirectory() as directory:
            model_dir = Path(directory)
            (model_dir / "model.bin").write_bytes(b"model")
            manifest = {
                "repository": "Systran/faster-whisper-base",
                "revision": "fixture-model-version",
                "model_sha256": hashlib.sha256(b"model").hexdigest(),
            }
            (model_dir / "kt-model.json").write_text(json.dumps(manifest))
            whisper = Mock()
            whisper.return_value.transcribe.return_value = (
                [SimpleNamespace(text="  Có lời nói  ", start=0.0, end=1.5)],
                SimpleNamespace(duration=2.0, language="vi", language_probability=0.95),
            )
            with (
                patch("processing.transcribe._media_duration", return_value=2.0),
                patch.dict(
                    sys.modules,
                    {"faster_whisper": SimpleNamespace(WhisperModel=whisper)},
                ),
            ):
                result = run(model_dir / "media", model_dir)
            self.assertEqual(result["segments"][0]["text"], "Có lời nói")
            self.assertTrue(whisper.call_args.kwargs["local_files_only"])
            self.assertEqual(whisper.call_args.kwargs["device"], "cpu")
            (model_dir / "model.bin").write_bytes(b"corrupt")
            with (
                patch("processing.transcribe._media_duration", return_value=2.0),
                patch.dict(
                    sys.modules,
                    {"faster_whisper": SimpleNamespace(WhisperModel=whisper)},
                ),
                self.assertRaisesRegex(ValueError, "checksum"),
            ):
                run(model_dir / "media", model_dir)


@override_settings(LOCAL_ASR_MODEL_DIR="fixture-local-model")
class TranscriptJobTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="transcript-owner")
        self.item = Item.objects.create(
            owner=self.owner,
            kind="link",
            title="Nội dung",
            note="Bài người dùng đã biên soạn",
        )
        self.event = CaptureEvent.objects.create(
            owner=self.owner,
            item=self.item,
            raw_kind="link",
            original_url="https://example.com/source",
        )
        self.payload = b"verified-media-fixture"
        self.asset = Asset.objects.create(
            item=self.item,
            role="original",
            mime="video/mp4",
            original_filename="source.mp4",
            size=len(self.payload),
            sha256=hashlib.sha256(self.payload).hexdigest(),
        )
        self.location = StorageLocation.objects.create(
            asset=self.asset,
            provider="google_drive",
            provider_file_id="fixture-only",
            status="verified",
            verified_at=timezone.now(),
        )
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.settings_context = override_settings(
            THUMBNAIL_CACHE_DIR=str(Path(self.directory.name) / "thumbnails")
        )
        self.settings_context.enable()
        self.addCleanup(self.settings_context.disable)
        self.storage = SimpleNamespace(
            stat=lambda asset: SimpleNamespace(
                file_id="fixture-only",
                sha256=asset.sha256,
                size=asset.size,
                mime=asset.mime,
            ),
            client=SimpleNamespace(
                api=SimpleNamespace(
                    files=lambda: SimpleNamespace(get_media=lambda **kwargs: None)
                ),
                call=lambda method: method(),
            ),
        )
        self.source_paths = []

    def claim(self):
        enqueue_transcript(self.asset)
        return JobRepository.claim(["transcribe_media"])

    def invoke(
        self, job, result, *, damage_download=False, expire_during_inference=False
    ):
        payload = b"corrupted-media" if damage_download else self.payload

        class Download:
            def __init__(self, stream, request, chunksize):
                self.stream = stream

            def next_chunk(self):
                self.stream.write(payload)
                return None, True

        def inference(path, model):
            self.source_paths.append(path)
            self.assertEqual(path.read_bytes(), self.payload)
            if expire_during_inference:
                Job.objects.filter(pk=job.pk).update(
                    lease_until=timezone.now() - timedelta(seconds=1)
                )
            return result

        with (
            patch(
                "processing.transcript_job.storage_for_owner", return_value=self.storage
            ),
            patch("processing.transcript_job.MediaIoBaseDownload", Download),
            patch("processing.transcript_job.transcribe_file", side_effect=inference),
        ):
            transcribe_media(job)

    def test_only_verified_originals_are_enqueued_and_done_job_does_not_reset_status(
        self,
    ):
        self.location.status = "pending"
        self.location.save(update_fields=["status"])
        self.assertFalse(enqueue_transcript(self.asset))
        self.assertFalse(Job.objects.filter(kind="transcribe_media").exists())
        self.location.status = "verified"
        self.location.save(update_fields=["status"])
        self.assertTrue(enqueue_transcript(self.asset))
        self.assertTrue(enqueue_transcript(self.asset))
        self.assertEqual(Job.objects.filter(kind="transcribe_media").count(), 1)
        Job.objects.filter(kind="transcribe_media").update(state="done")
        self.item.content_extract = "done"
        self.item.save(update_fields=["content_extract"])
        self.assertFalse(enqueue_transcript(self.asset))
        self.item.refresh_from_db()
        self.assertEqual(self.item.content_extract, "done")

    def test_valid_timed_text_is_versioned_idempotent_and_does_not_modify_authored_text_or_history(
        self,
    ):
        original_note, original_time = self.item.note, self.event.server_received_at
        job = self.claim()
        result = {
            "state": "done",
            "language": "vi",
            "model_revision": "fixture-model",
            "segments": [{"start": 2.5, "end": 4.0, "text": "Nội dung lời nói"}],
        }
        self.invoke(job, result)
        part = DerivedContent.objects.get(asset=self.asset)
        self.assertEqual(part.processor_version, PROCESSOR_VERSION)
        self.assertEqual(part.input_hash, self.asset.sha256)
        self.assertIn("[00:02–00:04]", part.text)
        self.assertEqual(part.source_locator["segments"], result["segments"])
        with patch("processing.transcript_job.storage_for_owner") as storage:
            transcribe_media(job)
            storage.assert_not_called()
        self.assertEqual(DerivedContent.objects.filter(asset=self.asset).count(), 1)
        self.item.refresh_from_db()
        self.event.refresh_from_db()
        self.assertEqual(self.item.note, original_note)
        self.assertEqual(self.event.server_received_at, original_time)
        self.assertFalse(self.source_paths[0].exists())

    def test_empty_audio_preserves_prior_usable_text_and_cleans_private_scratch(self):
        prior = DerivedContent.objects.create(
            item=self.item,
            asset=self.asset,
            kind="video_transcript",
            text="Bản trước",
            processor="previous",
            processor_version="previous",
            input_hash="b" * 64,
        )
        self.invoke(self.claim(), {"state": "not_available", "segments": []})
        prior.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(prior.status, "active")
        self.assertEqual(self.item.content_extract, "partial")
        self.assertFalse(self.source_paths[0].exists())

    def test_processing_error_status_is_failed_only_when_no_usable_text_exists(self):
        for note, expected in (("", "failed"), ("Bài vẫn đọc được", "partial")):
            self.item.note = note
            self.item.save(update_fields=["note"])
            job = self.claim()
            if job is None:
                job = Job.objects.get(kind="transcribe_media")
            with self.assertRaisesRegex(JobFailure, "transcript_processing_failed"):
                self.invoke(
                    job,
                    {
                        "state": "failed",
                        "error": "private exception details",
                        "segments": [],
                    },
                )
            self.item.refresh_from_db()
            self.assertEqual(self.item.content_extract, expected)
            self.assertFalse(DerivedContent.objects.exists())
            self.assertFalse(self.source_paths[-1].exists())

    def test_lost_lease_cannot_persist_or_change_status_after_inference(self):
        job = self.claim()
        with self.assertRaisesRegex(JobFailure, "transcript_lease_lost"):
            self.invoke(
                job,
                {
                    "state": "done",
                    "segments": [{"start": 0, "end": 1, "text": "Không được lưu"}],
                },
                expire_during_inference=True,
            )
        self.assertFalse(DerivedContent.objects.exists())
        self.item.refresh_from_db()
        self.assertEqual(self.item.content_extract, "pending")
        self.assertFalse(self.source_paths[0].exists())

    def test_corrupt_download_cannot_reach_inference_or_persist(self):
        with self.assertRaisesRegex(JobFailure, "transcript_source_changed"):
            self.invoke(
                self.claim(), {"state": "done", "segments": []}, damage_download=True
            )
        self.assertFalse(self.source_paths)
        self.assertFalse(DerivedContent.objects.exists())

    def test_retry_endpoint_queues_existing_video_without_new_capture_or_asset(self):
        self.item.source_fetch = "done"
        self.item.save(update_fields=["source_fetch"])
        self.client.force_login(self.owner)
        response = self.client.post(f"/api/v1/items/{self.item.pk}/retry")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["queued"], 1)
        self.assertEqual(Job.objects.filter(kind="transcribe_media").count(), 1)
        self.assertEqual(CaptureEvent.objects.count(), 1)
        self.assertEqual(Asset.objects.count(), 1)
        self.item.refresh_from_db()
        self.assertEqual(self.item.source_fetch, "done")
