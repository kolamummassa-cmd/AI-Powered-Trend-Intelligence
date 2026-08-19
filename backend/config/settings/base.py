"""
Base Django settings for AI-Powered Trend Intelligence.

Shared by every environment. Environment-specific overrides live in
dev.py and prod.py. Never put secrets or environment-specific values
directly in this file — read them from the environment via django-environ.
"""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
# Reads backend/.env if present. In containers/Render, real env vars take precedence.
environ.Env.read_env(str(BASE_DIR / ".env"))

SECRET_KEY = env("DJANGO_SECRET_KEY", default="unsafe-secret-key-override-in-env")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
]

# Feature apps are added here as each phase is built.
LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.trend_sources",
    "apps.trends",
    "apps.trend_analysis",
    "apps.content_studio",
    "apps.ai_chat",
    "apps.notifications",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgres://postgres:postgres@localhost:5432/trend_intelligence",
    )
}

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static & media files
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    # ScopedRateThrottle only fires on views that set throttle_scope, so
    # User/AnonRateThrottle are also listed as a catch-all floor for every
    # other endpoint (list/detail views, notifications, analytics, etc.)
    # that would otherwise have zero rate limiting.
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.ScopedRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "auth": "10/min",
        "ai_generation": "20/min",
        "user": "1000/day",
        "anon": "100/day",
    },
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}

# ---------------------------------------------------------------------------
# CORS / CSRF
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:3000"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=["http://localhost:3000"])

# ---------------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Single heartbeat task that checks every active Platform's due-ness and
# fans out — adding a platform never means touching this schedule.
CELERY_BEAT_SCHEDULE = {
    "poll-due-trend-platforms": {
        "task": "apps.trend_sources.tasks.poll_due_platforms",
        "schedule": 300.0,  # every 5 minutes
    },
    "check-trend-lifecycle": {
        "task": "apps.trends.tasks.check_trend_lifecycle",
        "schedule": 3600.0,  # hourly — ages trends into expiring/expired, fires alerts
    },
}

# ---------------------------------------------------------------------------
# AI providers (Phase 3 wires the actual client logic; keys live in env only)
# ---------------------------------------------------------------------------
AI_PROVIDER = env("AI_PROVIDER", default="claude")
OPENAI_API_KEY = env("OPENAI_API_KEY", default="")
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", default="")

# ---------------------------------------------------------------------------
# Auth (Phase 1)
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

GOOGLE_OAUTH_CLIENT_ID = env("GOOGLE_OAUTH_CLIENT_ID", default="")

# Where email links (verification, password reset) point to.
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@trendintelligence.app")

# ---------------------------------------------------------------------------
# Trend sources (Phase 2)
# ---------------------------------------------------------------------------
REDDIT_CLIENT_ID = env("REDDIT_CLIENT_ID", default="")
REDDIT_CLIENT_SECRET = env("REDDIT_CLIENT_SECRET", default="")
REDDIT_USER_AGENT = env("REDDIT_USER_AGENT", default="ai-trend-intelligence/0.1 (by Foluxnova)")

# ---------------------------------------------------------------------------
# Trend sources (Phase 9) — each requires its own developer/API access;
# see the adapter docstrings in apps/trend_sources/adapters.py for what
# tier/approval each one needs before a Platform row using it will work.
# ---------------------------------------------------------------------------
YOUTUBE_API_KEY = env("YOUTUBE_API_KEY", default="")
X_BEARER_TOKEN = env("X_BEARER_TOKEN", default="")
TIKTOK_RESEARCH_TOKEN = env("TIKTOK_RESEARCH_TOKEN", default="")
INSTAGRAM_ACCESS_TOKEN = env("INSTAGRAM_ACCESS_TOKEN", default="")
INSTAGRAM_BUSINESS_ACCOUNT_ID = env("INSTAGRAM_BUSINESS_ACCOUNT_ID", default="")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": env("DJANGO_LOG_LEVEL", default="INFO")},
}
