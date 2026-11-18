import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()

if settings.WEB_DIST:
    from pathlib import Path
    from whitenoise import WhiteNoise

    root = Path(settings.WEB_DIST)
    if not (root / "index.html").is_file():
        raise ImproperlyConfigured("Build the frontend before starting the Windows app.")

    def static_headers(headers, path, url):
        if Path(path).name == "index.html":
            headers["Cache-Control"] = "no-cache"

    application = WhiteNoise(
        application,
        root=str(root),
        prefix="",
        index_file=True,
        add_headers_function=static_headers,
    )
