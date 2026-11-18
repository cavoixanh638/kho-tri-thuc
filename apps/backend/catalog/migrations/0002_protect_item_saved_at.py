from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]

    operations = [
        migrations.RunSQL(
            """
            CREATE FUNCTION kt_protect_item_saved_at() RETURNS trigger
            LANGUAGE plpgsql AS $$
            BEGIN
                RAISE EXCEPTION 'Item.saved_at is immutable' USING ERRCODE = '23514';
            END;
            $$;
            CREATE TRIGGER kt_item_saved_at_immutable
            BEFORE UPDATE OF saved_at ON catalog_item
            FOR EACH ROW
            WHEN (OLD.saved_at IS DISTINCT FROM NEW.saved_at)
            EXECUTE FUNCTION kt_protect_item_saved_at();
            """,
            """
            DROP TRIGGER kt_item_saved_at_immutable ON catalog_item;
            DROP FUNCTION kt_protect_item_saved_at();
            """,
        ),
    ]
