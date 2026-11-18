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
