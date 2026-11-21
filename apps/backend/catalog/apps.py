from importlib import import_module

from django.apps import AppConfig


class CatalogConfig(AppConfig):
    name = "catalog"

    def import_models(self):
        super().import_models()
        # Keep independent feature models registered before migration checks.
        import_module("catalog.collection_models")
