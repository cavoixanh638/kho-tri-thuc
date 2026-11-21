import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0005_item_home_topic")]
    operations = [
        migrations.AddField(
            model_name="item",
            name="parent_item",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="structural_children",
                to="catalog.item",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="outline_order",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="item",
            name="structure_version",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="item",
            name="structure_origin",
            field=models.CharField(default="user", max_length=12),
        ),
        migrations.AddIndex(
            model_name="item",
            index=models.Index(
                fields=["owner", "home_topic", "parent_item", "outline_order", "id"],
                name="item_explorer_home_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="item",
            index=models.Index(
                fields=["owner", "parent_item", "outline_order", "id"],
                name="item_outline_parent_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="item",
            constraint=models.CheckConstraint(
                condition=~models.Q(id=models.F("parent_item_id")),
                name="item_not_own_parent",
            ),
        ),
    ]
