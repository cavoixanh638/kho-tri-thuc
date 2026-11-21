import uuid
from typing import ClassVar

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies: ClassVar = [
        ("catalog", "0006_item_structural_parent"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations: ClassVar = [
        migrations.CreateModel(
            name="SavedCollection",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=120)),
                ("normalized_name", models.CharField(max_length=240)),
                ("query", models.JSONField(default=dict)),
                ("view", models.CharField(default="list", max_length=12)),
                ("version", models.PositiveIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["owner", "name", "id"], name="collection_owner_name_idx"
                    )
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("owner", "normalized_name"),
                        name="collection_owner_name_uniq",
                    )
                ],
            },
        ),
    ]
