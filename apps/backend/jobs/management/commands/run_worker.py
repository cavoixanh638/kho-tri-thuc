import os
import signal
from time import monotonic
from threading import Event, Thread

from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, close_old_connections, connection

from config.health import check_database
from jobs.handlers import HANDLERS
from jobs.worker import Worker

POLL_SECONDS = 1


class Command(BaseCommand):
    help = "Run the PostgreSQL job worker."

    def add_arguments(self, parser):
        parser.add_argument(
            "--check",
            action="store_true",
            help="Check the database connection and exit.",
        )

    def handle(self, *args, **options):
        try:
            check_database()
        except DatabaseError as exc:
            raise CommandError("Worker could not connect to PostgreSQL.") from exc
        finally:
            connection.close()

        if options["check"]:
            self.stdout.write("Worker database check passed.")
            return

        stopped = Event()

        def stop(_signal_number, _frame):
            stopped.set()

        shutdown_signals = (signal.SIGINT, signal.SIGTERM)
        previous = {
            shutdown_signal: signal.signal(shutdown_signal, stop)
            for shutdown_signal in shutdown_signals
        }

        worker = Worker(HANDLERS)
        refresh_running = Event()
        catalog_thread = None
        next_catalog_tick = 0.0

        def refresh_catalog():
            from django.db import close_old_connections, connections
            from processing.gemini_catalog import refresh_if_due
            try:
                close_old_connections()
                refresh_if_due()
            except Exception:
                # Do not log remote responses or credentials.
                self.stderr.write("Gemini catalog background refresh unavailable.")
            finally:
                connections.close_all()
                refresh_running.clear()

        self.stdout.write("Worker started.")
        try:
            while not stopped.is_set():
                if os.getenv("GEMINI_API_KEY") and monotonic() >= next_catalog_tick:
                    next_catalog_tick = monotonic() + 600
                    if not refresh_running.is_set():
                        refresh_running.set()
                        catalog_thread = Thread(
                            target=refresh_catalog,
                            name="gemini-model-catalog",
                            daemon=True,
                        )
                        catalog_thread.start()
                close_old_connections()
                try:
                    worked = worker.run_once()
                except DatabaseError:
                    self.stderr.write("Worker database operation failed. Retrying.")
                    worked = False
                if not worked:
                    stopped.wait(POLL_SECONDS)
        finally:
            connection.close()
            for shutdown_signal, handler in previous.items():
                signal.signal(shutdown_signal, handler)
