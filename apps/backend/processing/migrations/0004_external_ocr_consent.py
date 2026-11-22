"""External image processing needs explicit consent per account (default off)."""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("processing", "0003_gemini_registry"),
    ]

    operations = [
        migrations.AddField(
            model_name="geminipreference",
            name="external_ocr_consent",
            field=models.BooleanField(default=False),
        ),
    ]
