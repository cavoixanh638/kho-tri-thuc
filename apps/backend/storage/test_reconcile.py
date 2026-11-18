import json
from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

from catalog.models import Item, ItemTopic, RelatedItem, Topic
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from ingestion.models import CaptureEvent
from processing.models import DerivedContent

from .drive import DriveClient, DriveError
from .models import Asset, StorageLocation
from .reconcile import RECONCILE_FIELDS, probe_location, reconcile_location


class DriveReconcileTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create(username="owner")
        cls.other_owner = get_user_model().objects.create(username="other-owner")
        cls.item = Item.objects.create(
            owner=cls.owner, kind=Item.Kind.FILE, note="Ghi chú riêng"
        )
        cls.related_item = Item.objects.create(owner=cls.owner, kind=Item.Kind.TEXT)
        item_a, item_b = sorted([cls.item, cls.related_item], key=lambda row: row.pk)
        cls.related = RelatedItem.objects.create(
            item_a=item_a,
            item_b=item_b,
            reason="derived similarity",
            method_version="test",
            source_version="test",
        )
        cls.capture = CaptureEvent.objects.create(
            owner=cls.owner,
            item=cls.item,
            raw_kind=CaptureEvent.Kind.TEXT,
            raw_text="Ghi chú gốc",
        )
        cls.topic = Topic.objects.create(owner=cls.owner, name="Nghiên cứu")
        cls.assignment = ItemTopic.objects.create(
            item=cls.item, topic=cls.topic, user_pinned=True
        )
        cls.asset = Asset.objects.create(
            item=cls.item,
            original_filename="goc.pdf",
            mime="application/pdf",
            size=100,
            sha256="a" * 64,
        )
        cls.location = StorageLocation.objects.create(
            asset=cls.asset,
            provider_file_id="drive-file",
            status=StorageLocation.Status.VERIFIED,
            provider_revision="1",
            verified_at=timezone.now(),
        )
        cls.derived = DerivedContent.objects.create(
            item=cls.item,
            asset=cls.asset,
            kind="pdf",
            text="Văn bản tệp",
            processor="pdf",
            processor_version="1",
            input_hash=cls.asset.sha256,
        )
        cls.web_content = DerivedContent.objects.create(
            item=cls.item,
            kind="website",
            text="Văn bản nguồn khác",
            processor="html",
            processor_version="1",
            input_hash="b" * 64,
        )

    def setUp(self):
        self.client = Mock(spec=DriveClient)
        self.account = SimpleNamespace(
            owner_id=self.owner.pk, root_folder_id="drive-root"
        )

    def metadata(self, **changes):
        return {
            "id": self.location.provider_file_id,
            "name": self.asset.original_filename,
            "parents": ["drive-root"],
            "size": str(self.asset.size),
            "mimeType": self.asset.mime,
            "sha256Checksum": self.asset.sha256,
            "version": "2",
            "modifiedTime": "2026-11-18T10:00:00Z",
            "trashed": False,
            "appProperties": {
                "kt_item_id": str(self.asset.item_id),
                "kt_asset_id": str(self.asset.pk),
            },
        } | changes

    def reconcile(self, location=None):
        return reconcile_location(
            location or self.location, client=self.client, account=self.account
        )

    def test_metadata_rename_and_move_preserve_name_and_derivatives(self):
        self.client.get_file.return_value = self.metadata(
            name="đổi-tên.pdf", parents=["other-folder"]
        )
        result = self.reconcile()
        self.client.get_file.assert_called_once_with("drive-file", RECONCILE_FIELDS)
        self.assertEqual(result.remote_name, "đổi-tên.pdf")
        self.assertTrue(result.outside_root)
        self.assertEqual(result.outcome, "verified")
        self.location.refresh_from_db()
        self.derived.refresh_from_db()
        self.asset.refresh_from_db()
        self.assertEqual(self.location.provider_revision, "2")
        self.assertEqual(self.asset.original_filename, "goc.pdf")
        self.assertEqual(self.derived.status, DerivedContent.Status.ACTIVE)

    def test_changed_digest_invalidates_once_and_leaves_original_identity_and_curated_data(
        self,
    ):
        self.client.get_file.return_value = self.metadata(sha256Checksum="c" * 64)
        first = self.reconcile()
        self.assertEqual(first.outcome, "content_changed")
        self.assertTrue(first.applied)
        self.location.refresh_from_db()
        self.asset.refresh_from_db()
        self.derived.refresh_from_db()
        self.web_content.refresh_from_db()
        self.related.refresh_from_db()
        self.capture.refresh_from_db()
        self.item.refresh_from_db()
        self.assignment.refresh_from_db()
        self.assertEqual(self.location.status, StorageLocation.Status.FAILED)
        self.assertEqual(self.location.asset_id, self.asset.pk)
        self.assertEqual(self.asset.sha256, "a" * 64)
        self.assertEqual(self.asset.size, 100)
        self.assertEqual(self.asset.content_version, 2)
        self.assertEqual(self.derived.status, DerivedContent.Status.STALE)
        self.assertEqual(self.web_content.status, DerivedContent.Status.ACTIVE)
        self.assertEqual(self.related.status, RelatedItem.Status.STALE)
        self.assertEqual(self.capture.raw_text, "Ghi chú gốc")
        self.assertEqual(self.item.note, "Ghi chú riêng")
        self.assertTrue(self.assignment.user_pinned)
        self.assertFalse(self.reconcile().applied)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.content_version, 2)

    def test_404_and_403_are_inaccessible_and_explicit_trash_is_missing(self):
        for failure in (
            DriveError("drive_not_found", status=404),
            DriveError("drive_request_failed", status=403),
        ):
            self.client.get_file.side_effect = failure
            self.assertEqual(self.reconcile().outcome, "inaccessible")
            self.location.refresh_from_db()
            self.assertEqual(self.location.status, StorageLocation.Status.INACCESSIBLE)
            self.assertEqual(self.location.provider_file_id, "drive-file")
        self.client.get_file.side_effect = None
        self.client.get_file.return_value = self.metadata(trashed=True)
        self.assertEqual(self.reconcile().outcome, "trashed")
        self.location.refresh_from_db()
        self.assertEqual(self.location.status, StorageLocation.Status.MISSING)
        self.assertEqual(self.location.provider_file_id, "drive-file")

    def test_wrong_owner_or_missing_app_properties_do_not_verify_a_mapping(self):
        with self.assertRaisesRegex(DriveError, "storage_owner_mismatch"):
            probe_location(
                self.location,
                client=self.client,
                account=SimpleNamespace(owner_id=self.other_owner.pk),
            )
        self.client.get_file.assert_not_called()
        self.client.get_file.return_value = self.metadata(appProperties={})
        self.assertEqual(self.reconcile().outcome, "identity_mismatch")
        self.location.refresh_from_db()
        self.assertEqual(self.location.status, StorageLocation.Status.INACCESSIBLE)

    def test_missing_checksum_on_a_new_revision_cannot_reverify_old_bytes(self):
        self.client.get_file.return_value = self.metadata(sha256Checksum=None)
        self.assertEqual(self.reconcile().outcome, "content_unverified")
        self.location.refresh_from_db()
        self.derived.refresh_from_db()
        self.assertEqual(self.location.status, StorageLocation.Status.FAILED)
        self.assertEqual(self.derived.status, DerivedContent.Status.ACTIVE)

        self.client.get_file.return_value = self.metadata(sha256Checksum="c" * 64)
        self.assertEqual(self.reconcile().outcome, "content_changed")
        self.derived.refresh_from_db()
        self.assertEqual(self.derived.status, DerivedContent.Status.STALE)

    def test_retryable_failure_preserves_status_and_pending_reservation_is_not_downgraded(
        self,
    ):
        self.client.get_file.side_effect = DriveError(
            "drive_unavailable", status=429, retryable=True
        )
        with self.assertRaisesRegex(DriveError, "drive_unavailable"):
            self.reconcile()
        self.location.refresh_from_db()
        self.assertEqual(self.location.status, StorageLocation.Status.VERIFIED)
        self.location.status = StorageLocation.Status.PENDING
        self.location.save(update_fields=["status"])
        self.client.get_file.side_effect = DriveError("drive_not_found", status=404)
        self.assertFalse(self.reconcile().applied)
        self.location.refresh_from_db()
        self.assertEqual(self.location.status, StorageLocation.Status.PENDING)

    def test_concurrent_newer_mapping_is_not_overwritten(self):
        def network_get(*args):
            StorageLocation.objects.filter(pk=self.location.pk).update(
                provider_revision="3"
            )
            return self.metadata()

        self.client.get_file.side_effect = network_get
        self.assertEqual(self.reconcile().outcome, "superseded")
        self.location.refresh_from_db()
        self.assertEqual(self.location.provider_revision, "3")

    def test_probe_command_only_reads_the_requested_owner_and_bounds_batch(self):
        additional = Asset.objects.create(
            item=self.item, original_filename="another.pdf", mime="application/pdf"
        )
        StorageLocation.objects.create(
            asset=additional, provider_file_id="another-file"
        )
        other_item = Item.objects.create(owner=self.other_owner, kind=Item.Kind.FILE)
        other_asset = Asset.objects.create(
            item=other_item, original_filename="other.pdf", mime="application/pdf"
        )
        StorageLocation.objects.create(asset=other_asset, provider_file_id="other-file")
        self.client.get_file.return_value = self.metadata(sha256Checksum="c" * 64)

        output = StringIO()
        with patch(
            "storage.management.commands.reconcile_drive._read_only_client",
            return_value=(self.client, self.account),
        ):
            call_command(
                "reconcile_drive", owner_id=self.owner.pk, limit=1, stdout=output
            )

        data = json.loads(output.getvalue())
        self.assertEqual(data["next_after_location"], self.location.pk)
        self.assertEqual(data["results"][0]["outcome"], "content_changed")
        self.assertFalse(data["results"][0]["applied"])
        self.client.get_file.assert_called_once_with("drive-file", RECONCILE_FIELDS)
        self.location.refresh_from_db()
        self.asset.refresh_from_db()
        self.assertEqual(self.location.status, StorageLocation.Status.VERIFIED)
        self.assertEqual(self.asset.content_version, 1)
