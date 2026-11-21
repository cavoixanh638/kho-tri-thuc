from uuid import uuid4

from django.db import models
from django.db.models import Q

from catalog.models import Item
from storage.models import Asset


class DerivedContent(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        STALE = "stale", "Stale"
        FAILED = "failed", "Failed"

    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="derived_content"
    )
    asset = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT,
        related_name="derived_content",
        null=True,
        blank=True,
    )
    kind = models.CharField(max_length=32)
    text = models.TextField(blank=True)
    source_locator = models.JSONField(default=dict, blank=True)
    processor = models.CharField(max_length=64)
    processor_version = models.CharField(max_length=64)
    input_hash = models.CharField(max_length=64)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["item", "kind"],
                condition=Q(status="active"),
                name="derived_item_kind_active_idx",
            ),
        ]


class ClipAnnotation(models.Model):
    """An immutable source excerpt, separate from the author's note."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="clips")
    capture = models.OneToOneField(
        "ingestion.CaptureEvent", on_delete=models.PROTECT, related_name="clip"
    )
    source = models.ForeignKey(
        "catalog.Source", null=True, on_delete=models.PROTECT, related_name="clips"
    )
    part = models.ForeignKey(
        DerivedContent, null=True, on_delete=models.PROTECT, related_name="clips"
    )
    asset = models.ForeignKey(Asset, null=True, on_delete=models.PROTECT)
    mode = models.CharField(max_length=12)
    quote = models.TextField(blank=True)
    quote_hash = models.CharField(max_length=64, blank=True)
    source_version = models.CharField(max_length=64, blank=True)
    processor_version = models.CharField(max_length=64, blank=True)
    locator = models.JSONField(default=dict)
    source_url = models.TextField(blank=True)
    page_title = models.CharField(max_length=512, blank=True)
    verification = models.CharField(max_length=24, default="unverified")
    inserted_edit_version = models.PositiveIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["item", "-created_at", "id"], name="clip_item_created_idx"
            )
        ]
