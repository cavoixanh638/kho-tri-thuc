"""Saved owner-scoped query definitions; never materialized Item memberships."""

from typing import ClassVar
from uuid import uuid4

from django.conf import settings
from django.db import models


class SavedCollection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    name = models.CharField(max_length=120)
    normalized_name = models.CharField(max_length=240)
    query = models.JSONField(default=dict)
    view = models.CharField(max_length=12, default="list")
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "catalog"
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=["owner", "normalized_name"], name="collection_owner_name_uniq"
            ),
        ]
        indexes: ClassVar = [
            models.Index(
                fields=["owner", "name", "id"], name="collection_owner_name_idx"
            ),
        ]
