from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from catalog.models import Item

from .models import Asset, StorageLocation


class StorageSchemaTests(TestCase):
    def test_remote_location_requires_verified_evidence_without_replacing_asset_id(
        self,
    ):
        owner = get_user_model().objects.create(username="owner")
        item = Item.objects.create(owner=owner, kind=Item.Kind.FILE)
        asset = Asset.objects.create(
            item=item, mime="image/png", original_filename="ảnh.png"
        )
        asset_id = asset.pk

        location = StorageLocation.objects.create(asset=asset)
        location.status = StorageLocation.Status.VERIFIED
        with self.assertRaises(IntegrityError), transaction.atomic():
            location.save()

        location.provider_file_id = "drive-id"
        location.verified_at = timezone.now()
        location.save()
        asset.refresh_from_db()
        self.assertEqual(asset.pk, asset_id)
        self.assertEqual(asset.locations.get().provider_file_id, "drive-id")
