from uuid import uuid4

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from catalog.models import Item


class CaptureEvent(models.Model):
    class Kind(models.TextChoices):
        LINK = "link", "Link"
        TEXT = "text", "Text"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="captures")
    source_channel = models.CharField(max_length=32, default="web")
    raw_kind = models.CharField(max_length=12, choices=Kind.choices)
    raw_text = models.TextField(blank=True)
    original_url = models.TextField(blank=True)
    server_received_at = models.DateTimeField(default=timezone.now, editable=False)
    client_sent_at = models.DateTimeField(null=True, blank=True)
    idempotency_key = models.CharField(max_length=128, null=True, blank=True)
    status = models.CharField(max_length=24, default="received")

    class Meta:
        indexes = [
            models.Index(
                fields=["owner", "-server_received_at", "id"],
                name="capture_owner_received_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "source_channel", "idempotency_key"],
                condition=Q(idempotency_key__isnull=False),
                name="capture_request_key_uniq",
            ),
            models.CheckConstraint(
                condition=(Q(raw_kind="link") & ~Q(original_url=""))
                | (Q(raw_kind="text", original_url="") & ~Q(raw_text="")),
                name="capture_raw_input_ck",
            ),
        ]
