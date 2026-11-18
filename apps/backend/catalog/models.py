from uuid import uuid4

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class Item(models.Model):
    class Kind(models.TextChoices):
        LINK = "link", "Link"
        TEXT = "text", "Text"
        FILE = "file", "File"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    kind = models.CharField(max_length=12, choices=Kind.choices)
    title = models.CharField(max_length=512, blank=True)
    description = models.TextField(blank=True)
    note = models.TextField(blank=True)
    saved_at = models.DateTimeField(default=timezone.now, editable=False)
    published_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    favorite = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    user_edit_version = models.PositiveIntegerField(default=0)
    classification_status = models.CharField(max_length=24, default="pending")

    class Meta:
        indexes = [
            models.Index(
                fields=["owner", "-saved_at", "id"],
                name="item_owner_saved_idx",
                condition=Q(deleted_at__isnull=True),
            ),
        ]


class Source(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="sources")
    original_url = models.TextField()
    canonical_url = models.TextField()
    identity_hash = models.CharField(max_length=64, db_index=True)
    platform = models.CharField(max_length=24, default="web")
    platform_id = models.CharField(max_length=255, blank=True)
    captured_at = models.DateTimeField(default=timezone.now)
    published_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)


class Topic(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    name = models.CharField(max_length=120)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children"
    )
    archived = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "parent", "name"],
                nulls_distinct=False,
                name="topic_owner_parent_name_uniq",
            ),
        ]


class Project(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    archived = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name"], name="project_owner_name_uniq"
            ),
        ]


class Tag(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    name = models.CharField(max_length=120)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name"], name="tag_owner_name_uniq"
            ),
        ]


class Assignment(models.Model):
    class Origin(models.TextChoices):
        USER = "user", "User"
        AUTO = "auto", "Automatic"

    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    origin = models.CharField(
        max_length=12, choices=Origin.choices, default=Origin.USER
    )
    user_pinned = models.BooleanField(default=False)
    confidence = models.FloatField(null=True, blank=True)
    method_version = models.CharField(max_length=64, blank=True)
    source_version = models.CharField(max_length=128, blank=True)

    class Meta:
        abstract = True


class ItemTopic(Assignment):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["item", "topic"], name="item_topic_uniq"),
        ]


class ItemProject(Assignment):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["item", "project"], name="item_project_uniq"
            ),
        ]


class ItemTag(Assignment):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["item", "tag"], name="item_tag_uniq"),
        ]


class RelatedItem(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        STALE = "stale", "Stale"
        DISMISSED = "dismissed", "Dismissed"

    item_a = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="relations_a"
    )
    item_b = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="relations_b"
    )
    relation_type = models.CharField(max_length=32, default="similar")
    reason = models.TextField()
    confidence = models.FloatField(null=True, blank=True)
    method_version = models.CharField(max_length=64)
    source_version = models.CharField(max_length=128)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.ACTIVE
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(item_a__lt=F("item_b")), name="related_pair_order_ck"
            ),
            models.UniqueConstraint(
                fields=["item_a", "item_b"], name="related_pair_uniq"
            ),
        ]
