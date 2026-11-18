from django.db import migrations


def functions(note_limit, description_limit):
    return f"""
    CREATE OR REPLACE FUNCTION public.kt_search_item(title text, description text, note text)
    RETURNS text LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
    AS $$
        SELECT normalize(title || ' ' || left(description, {description_limit})
                               || ' ' || left(note, {note_limit}), NFC)
    $$;
    REINDEX INDEX public.kt_item_fts_gin;
    REINDEX INDEX public.kt_item_trgm_gin;
    """


class Migration(migrations.Migration):
    dependencies = [("search", "0001_search_indexes")]
    operations = [migrations.RunSQL(functions(100000, 20000), functions(40000, 40000))]
