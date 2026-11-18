import os

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.getenv("DJANGO_DEBUG") == "1"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "ninja",
    "catalog",
    "ingestion",
    "storage",
    "processing",
    "search",
    "jobs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.environ["POSTGRES_HOST"],
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "OPTIONS": {"connect_timeout": 3},
    }
}

LANGUAGE_CODE = "vi"
TIME_ZONE = "UTC"
USE_TZ = True
STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
    }
]

GOOGLE_DRIVE_CLIENT_ID = os.getenv("GOOGLE_DRIVE_CLIENT_ID", "")
GOOGLE_DRIVE_CLIENT_SECRET = os.getenv("GOOGLE_DRIVE_CLIENT_SECRET", "")
GOOGLE_DRIVE_REDIRECT_URI = os.getenv("GOOGLE_DRIVE_REDIRECT_URI", "")
GOOGLE_DRIVE_TOKEN_KEY = os.getenv("GOOGLE_DRIVE_TOKEN_KEY", "")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "oauth_callback": {"()": "config.access_log.SkipOAuthCallbackQuery"},
    },
    "handlers": {
        "server_console": {
            "class": "logging.StreamHandler",
            "filters": ["oauth_callback"],
        },
    },
    "loggers": {
        "django.server": {"handlers": ["server_console"], "level": "INFO", "propagate": False},
    },
}

UPLOAD_STAGING_ROOT = os.getenv("UPLOAD_STAGING_ROOT", "/var/lib/kho-tri-thuc/staging")
THUMBNAIL_CACHE_DIR = os.getenv("THUMBNAIL_CACHE_DIR", "/var/lib/kho-tri-thuc/thumbnails")
WEB_DIST = os.getenv("WEB_DIST", "")
