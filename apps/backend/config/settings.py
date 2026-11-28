import os

from search.prepare_bge import model_directory

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
        "django.server": {
            "handlers": ["server_console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

UPLOAD_STAGING_ROOT = os.getenv("UPLOAD_STAGING_ROOT", "/var/lib/kho-tri-thuc/staging")
THUMBNAIL_CACHE_DIR = os.getenv(
    "THUMBNAIL_CACHE_DIR", "/var/lib/kho-tri-thuc/thumbnails"
)
WEB_DIST = os.getenv("WEB_DIST", "")
FFMPEG_BINARY = os.getenv("FFMPEG_BINARY", "ffmpeg")
FFPROBE_BINARY = os.getenv("FFPROBE_BINARY", "ffprobe")
LOCAL_ASR_MODEL_DIR = os.getenv("LOCAL_ASR_MODEL_DIR", "")
_bge_model_dir = model_directory()
SEARCH_BGE_MODEL_DIR = str(_bge_model_dir) if _bge_model_dir is not None else ""
SEARCH_MEMORY_CANDIDATES = os.getenv("SEARCH_MEMORY_CANDIDATES", "0") == "1"
SEARCH_QUOTE_EVIDENCE_ENABLED = os.getenv("SEARCH_QUOTE_EVIDENCE_ENABLED", "0") == "1"
SEARCH_QUOTE_READER_URL = os.getenv("SEARCH_QUOTE_READER_URL", "http://127.0.0.1:19587/v1/chat/completions")
SEARCH_QUOTE_READER_MODEL = os.getenv("SEARCH_QUOTE_READER_MODEL", "qwen3-4b-instruct-2507-q4_k_m")
SEARCH_QUOTE_TIMEOUT_SECONDS = max(1, min(120, int(os.getenv("SEARCH_QUOTE_TIMEOUT_SECONDS", "45"))))
# Explicit development opt-in. This enables manual review only, never an AI provider.
SUGGESTION_REVIEW_POC_ENABLED = os.getenv("SUGGESTION_REVIEW_POC_ENABLED", "0") == "1"

# Provider credentials live only on the server. Discovery is read-only.
# Future OCR requests MUST be opt-in with an explicit cost/usage policy.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_ALLOW_PREMIUM_MODELS = os.getenv("GEMINI_ALLOW_PREMIUM_MODELS", "0") == "1"
GEMINI_OCR_ENABLED = os.getenv("GEMINI_OCR_ENABLED", "0") == "1"
GEMINI_MAX_LOCAL_REQUESTS_PER_DAY = max(
    0, min(100_000, int(os.getenv("GEMINI_MAX_LOCAL_REQUESTS_PER_DAY", "80")))
)

# Separate consent to transmit private image pixels to an external provider.
# Both flags must be enabled explicitly; defaults make zero Gemini image calls.
GEMINI_OCR_EXTERNAL_PROCESSING_ALLOWED = os.getenv(
    "GEMINI_OCR_EXTERNAL_PROCESSING_ALLOWED", "0"
) == "1"

# Model IDs require a successful OCR quality benchmark & explicit operator approval.
# PR82 reviewed model profiles alone do not authorize external inference.
GEMINI_OCR_APPROVED_MODELS = frozenset(
    item.strip() for item in os.getenv("GEMINI_OCR_APPROVED_MODELS", "").split(",")
    if item.strip()
)
