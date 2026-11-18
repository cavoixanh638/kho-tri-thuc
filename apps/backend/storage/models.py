from uuid import uuid4

from django.conf import settings
from django.db import models
from django.db.models import Q

from catalog.models import Item


class Asset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="assets")
    role = models.CharField(max_length=24, default="original")
    mime = models.CharField(max_length=255)
    size = models.PositiveBigIntegerField(null=True, blank=True)
    sha256 = models.CharField(max_length=64, blank=True)
    original_filename = models.CharField(max_length=255)
    content_version = models.PositiveIntegerField(default=1)


class StorageLocation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"
        FAILED = "failed", "Failed"
        MISSING = "missing", "Missing"
        INACCESSIBLE = "inaccessible", "Inaccessible"

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="locations")
    provider = models.CharField(max_length=32, default="google_drive")
    provider_file_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    provider_modified_at = models.DateTimeField(null=True, blank=True)
    provider_revision = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["asset", "provider"], name="asset_provider_uniq"
            ),
            models.UniqueConstraint(
                fields=["provider", "provider_file_id"], name="provider_file_id_uniq"
            ),
            models.CheckConstraint(
                condition=~Q(status="verified")
                | (
                    Q(provider_file_id__isnull=False, verified_at__isnull=False)
                    & ~Q(provider_file_id="")
                ),
                name="location_verified_requires_file_ck",
            ),
        ]


class DriveAccount(models.Model):
    class State(models.TextChoices):
        PENDING = "pending", "Pending"
        CONNECTED = "connected", "Connected"
        REAUTHORIZE = "reauthorize", "Reauthorize"

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="drive_account"
    )
    google_user_id = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True)
    root_folder_id = models.CharField(max_length=255, blank=True)
    refresh_token_ciphertext = models.TextField(blank=True)
    state = models.CharField(
        max_length=16, choices=State.choices, default=State.PENDING
    )
    connected_at = models.DateTimeField(null=True, blank=True)
