from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("catalog", "0004_knowledge_tree")]
    operations = [
        migrations.AddField(
            model_name="item", name="home_topic",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="home_items", to="catalog.topic"),
        ),
    ]
