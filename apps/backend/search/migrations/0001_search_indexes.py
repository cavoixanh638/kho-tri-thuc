from django.db import migrations


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("catalog", "0002_protect_item_saved_at"),
        ("ingestion", "0002_protect_capture_history"),
        ("processing", "0001_initial"),
    ]

    operations = [
        # Extensions are shared database infrastructure and may already exist.
        migrations.RunSQL(
            """
            CREATE EXTENSION IF NOT EXISTS unaccent WITH SCHEMA public;
            CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            """
            CREATE TEXT SEARCH CONFIGURATION public.kt_vi (COPY = pg_catalog.simple);
            ALTER TEXT SEARCH CONFIGURATION public.kt_vi
                ALTER MAPPING FOR asciiword, asciihword, hword_asciipart,
                                  word, hword, hword_part, numword, numhword,
                                  hword_numpart
                WITH public.unaccent, pg_catalog.simple;

            -- Keep indexed documents within the PostgreSQL tsvector size limit.
            CREATE FUNCTION public.kt_search_item(title text, description text, note text)
            RETURNS text LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
            AS $$
                SELECT normalize(title || ' ' || left(description, 40000)
                                       || ' ' || left(note, 40000), NFC)
            $$;

            CREATE FUNCTION public.kt_search_text(body text)
            RETURNS text LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
            AS $$ SELECT normalize(left(body, 80000), NFC) $$;

            -- Fixed one-character mappings for Vietnamese trigram/substring matches.
            -- Full-text search uses the kt_vi dictionary instead.
            CREATE FUNCTION public.kt_search_fold(body text)
            RETURNS text LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
            AS $$
                SELECT lower(translate(normalize(body, NFC),
                    'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ'
                    'ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ',
                    'aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyyd'
                    'aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyyd'))
            $$;

            CREATE INDEX kt_item_fts_gin ON catalog_item USING gin (
                to_tsvector('public.kt_vi', public.kt_search_item(title, description, note))
            ) WHERE deleted_at IS NULL;

            CREATE INDEX kt_derived_fts_gin ON processing_derivedcontent USING gin (
                to_tsvector('public.kt_vi', public.kt_search_text(text))
            ) WHERE status = 'active';

            CREATE INDEX kt_item_trgm_gin ON catalog_item USING gin (
                public.kt_search_fold(public.kt_search_item(title, description, note))
                public.gin_trgm_ops
            ) WHERE deleted_at IS NULL;
            """,
            reverse_sql="""
            DROP INDEX public.kt_item_trgm_gin;
            DROP INDEX public.kt_derived_fts_gin;
            DROP INDEX public.kt_item_fts_gin;
            DROP FUNCTION public.kt_search_fold(text);
            DROP FUNCTION public.kt_search_text(text);
            DROP FUNCTION public.kt_search_item(text, text, text);
            DROP TEXT SEARCH CONFIGURATION public.kt_vi;
            """,
        ),
    ]
