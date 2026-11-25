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


class GeminiModelCatalog(models.Model):
    """Untrusted discovery metadata; 'reviewed' does not mean quota is available."""

    model_id = models.CharField(max_length=128, primary_key=True)
    label = models.CharField(max_length=128)
    description = models.CharField(max_length=512, blank=True)
    generation_methods = models.JSONField(default=list)
    input_token_limit = models.PositiveIntegerField(default=0)
    output_token_limit = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    reviewed = models.BooleanField(default=False)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField()
    missing_sync_count = models.PositiveSmallIntegerField(default=0)


class GeminiCatalogState(models.Model):
    """Singleton scheduler lease; failure never clears the last good catalog."""

    id = models.PositiveSmallIntegerField(primary_key=True, default=1)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    next_refresh_at = models.DateTimeField(null=True, blank=True)
    last_error_code = models.CharField(max_length=48, blank=True)
    discovered_count = models.PositiveIntegerField(default=0)
    newly_discovered = models.PositiveIntegerField(default=0)


class GeminiPreference(models.Model):
    class Mode(models.TextChoices):
        ECONOMY = "economy", "Tiết kiệm"
        BALANCED = "balanced", "Tự động - cân bằng"
        QUALITY = "quality", "Chất lượng cao"
        MANUAL = "manual", "Chọn thủ công"

    owner = models.OneToOneField(
        "auth.User", on_delete=models.CASCADE, related_name="gemini_preference"
    )
    mode = models.CharField(max_length=16, choices=Mode.choices, default=Mode.BALANCED)
    manual_model_id = models.CharField(max_length=128, blank=True)
    # Explicit per-account consent before externally processing original photos.
    external_ocr_consent = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)


class GeminiUsageEvent(models.Model):
    """Local observation only. Never call this the provider's remaining quota."""

    owner = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="gemini_usage"
    )
    model_id = models.CharField(max_length=128)
    task = models.CharField(max_length=24)
    status = models.CharField(max_length=24)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    provider_error_code = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["model_id", "-created_at"],
                name="gemini_usage_model_idx",
            )
        ]
