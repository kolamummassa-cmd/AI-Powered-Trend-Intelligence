"""
Root URL configuration.

Feature apps mount their own urls.py under /api/v1/<feature>/ as each
phase is built (e.g. /api/v1/auth/, /api/v1/trends/). Versioning the
API prefix from day one avoids a breaking migration later.
"""

from django.contrib import admin
from django.urls import include, path

from apps.core.views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", health_check, name="health-check"),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/trends/", include("apps.trends.urls")),
    path("api/v1/content/", include("apps.content_studio.urls")),
    path("api/v1/chat/", include("apps.ai_chat.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
]
