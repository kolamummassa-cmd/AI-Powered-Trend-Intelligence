from .base import *  # noqa: F401,F403
from .base import env

DEBUG = True
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INSTALLED_APPS += ["django_extensions"]  # noqa: F405

CORS_ALLOW_ALL_ORIGINS = True

# Runs Celery tasks synchronously, in-process, by default in dev — no
# Redis, no separate worker/beat process required just to try the
# trend-ingestion pipeline locally. Set CELERY_TASK_ALWAYS_EAGER=False
# in your .env once you do want to run a real worker + beat locally
# (e.g. to test scheduling/retry behaviour, not just the task logic).
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=True)
CELERY_TASK_EAGER_PROPAGATES = True
