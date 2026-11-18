from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("jobs", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="job",
            name="lease_token",
            field=models.UUIDField(blank=True, editable=False, null=True),
        ),
    ]
