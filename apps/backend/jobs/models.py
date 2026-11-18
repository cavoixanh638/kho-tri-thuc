from uuid import uuid4

from django.db import models
from django.db.models import Q
from django.utils import timezone

from catalog.models import Item


class Job(models.Model):
    class State(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        RETRY = "retry", "Retry"
        FAILED = "failed", "Failed"
        DONE = "done", "Done"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="jobs", null=True, blank=True
    )
    kind = models.CharField(max_length=48)
    idempotency_key = models.CharField(max_length=128)
    state = models.CharField(max_length=12, choices=State.choices, default=State.QUEUED)
    attempt = models.PositiveIntegerField(default=0)
    retry_at = models.DateTimeField(default=timezone.now)
    lease_until = models.DateTimeField(null=True, blank=True)
    lease_token = models.UUIDField(blank=True, editable=False, null=True)
    error_code = models.CharField(max_length=64, blank=True)
    input_ref = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["retry_at", "created_at"],
                condition=Q(state__in=["queued", "retry"]),
                name="job_ready_idx",
            ),
            models.Index(
                fields=["lease_until"],
                condition=Q(state="running"),
                name="job_expired_lease_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "idempotency_key"], name="job_kind_key_uniq"
            ),
        ]
