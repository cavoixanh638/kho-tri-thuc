# Gemini OCR model catalog and local usage (not remote quota), 2026-11-21

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("processing", "0002_clip_annotations"),
    ]

    operations = [
        migrations.CreateModel(
            name="GeminiCatalogState",
            fields=[
                ("id", models.PositiveSmallIntegerField(default=1, primary_key=True, serialize=False)),
                ("last_attempt_at", models.DateTimeField(blank=True, null=True)),
                ("last_success_at", models.DateTimeField(blank=True, null=True)),
                ("next_refresh_at", models.DateTimeField(blank=True, null=True)),
                ("last_error_code", models.CharField(blank=True, max_length=48)),
                ("discovered_count", models.PositiveIntegerField(default=0)),
                ("newly_discovered", models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="GeminiModelCatalog",
            fields=[
                ("model_id", models.CharField(max_length=128, primary_key=True, serialize=False)),
                ("label", models.CharField(max_length=128)),
                ("description", models.CharField(blank=True, max_length=512)),
                ("generation_methods", models.JSONField(default=list)),
                ("input_token_limit", models.PositiveIntegerField(default=0)),
                ("output_token_limit", models.PositiveIntegerField(default=0)),
                ("active", models.BooleanField(default=True)),
                ("reviewed", models.BooleanField(default=False)),
                ("first_seen_at", models.DateTimeField(auto_now_add=True)),
                ("last_seen_at", models.DateTimeField()),
                ("missing_sync_count", models.PositiveSmallIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="GeminiPreference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("mode", models.CharField(choices=[
                    ("economy", "Tiết kiệm"), ("balanced", "Tự động - cân bằng"),
                    ("quality", "Chất lượng cao"), ("manual", "Chọn thủ công")
                ], default="balanced", max_length=16)),
                ("manual_model_id", models.CharField(blank=True, max_length=128)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("owner", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="gemini_preference", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="GeminiUsageEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("model_id", models.CharField(max_length=128)),
                ("task", models.CharField(max_length=24)),
                ("status", models.CharField(max_length=24)),
                ("input_tokens", models.PositiveIntegerField(default=0)),
                ("output_tokens", models.PositiveIntegerField(default=0)),
                ("provider_error_code", models.CharField(blank=True, max_length=40)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="gemini_usage", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "indexes": [models.Index(fields=["model_id", "-created_at"], name="gemini_usage_model_idx")],
            },
        ),
    ]
