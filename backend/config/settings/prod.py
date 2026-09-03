from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403
from .base import SECRET_KEY, env

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")  # must be explicitly set in production

# Defense-in-depth: render.yaml already sets `generateValue: true` for
# DJANGO_SECRET_KEY, so this should never actually trigger — but if that
# env var were ever unset for any reason, fail loudly at startup instead
# of silently running production on the publicly-known insecure default.
if SECRET_KEY == "unsafe-secret-key-override-in-env":
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY is not set — refusing to run with the insecure default in production."
    )

# ---------------------------------------------------------------------------
# Cache — shared Redis backend so multiple gunicorn workers (and the
# dashboard-stats/analytics-summary caching added in Phase 10) see the
# same cache instead of each worker holding its own in-memory copy.
# Dev intentionally stays on Django's default LocMemCache so running
# the app locally doesn't require Redis to be up.
# ---------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://localhost:6379/0"),
    }
}

# HTTPS / cookie hardening — Render terminates TLS in front of the app,
# so we trust the forwarded proto header to know the original request was HTTPS.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

CORS_ALLOW_ALL_ORIGINS = False
