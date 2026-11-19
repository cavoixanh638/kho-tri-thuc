from django.apps import AppConfig


class StorageConfig(AppConfig):
    name = "storage"

    def ready(self):
        from . import knowledge_signals  # noqa: F401 - register opt-in invalidation
