import signal
from threading import Event

from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, connection

from config.health import check_database


class Command(BaseCommand):
    help = "Start the scaffold worker and wait for shutdown."

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

        for shutdown_signal in (signal.SIGINT, signal.SIGTERM):
            signal.signal(shutdown_signal, stop)

        self.stdout.write("Worker started (scaffold).")
        stopped.wait()
