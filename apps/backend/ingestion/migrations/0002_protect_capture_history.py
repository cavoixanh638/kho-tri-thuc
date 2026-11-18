from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("ingestion", "0001_initial")]

    operations = [
        migrations.RunSQL(
            """
            CREATE FUNCTION kt_protect_capture_history() RETURNS trigger
            LANGUAGE plpgsql AS $$
            BEGIN
                RAISE EXCEPTION 'CaptureEvent input and history are immutable'
                    USING ERRCODE = '23514';
            END;
            $$;
            CREATE TRIGGER kt_capture_history_immutable
            BEFORE UPDATE ON ingestion_captureevent
            FOR EACH ROW
            WHEN (
                ROW(OLD.id, OLD.owner_id, OLD.item_id, OLD.source_channel,
                    OLD.raw_kind, OLD.raw_text, OLD.original_url,
                    OLD.server_received_at, OLD.client_sent_at, OLD.idempotency_key)
                IS DISTINCT FROM
                ROW(NEW.id, NEW.owner_id, NEW.item_id, NEW.source_channel,
                    NEW.raw_kind, NEW.raw_text, NEW.original_url,
                    NEW.server_received_at, NEW.client_sent_at, NEW.idempotency_key)
            )
            EXECUTE FUNCTION kt_protect_capture_history();
            """,
            """
            DROP TRIGGER kt_capture_history_immutable ON ingestion_captureevent;
            DROP FUNCTION kt_protect_capture_history();
            """,
        ),
    ]
