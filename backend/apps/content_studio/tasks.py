import logging

from celery import shared_task
from django.contrib.auth import get_user_model

from apps.content_studio.models import ContentBrief
from apps.content_studio.services import generate_brief, generate_content
from apps.notifications.models import NotificationType
from apps.notifications.services import notify_user
from apps.trends.models import Trend

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def generate_brief_task(self, trend_id: str, user_id: str | None = None):
    """Async wrapper around generate_brief — used for bulk/background
    regeneration; the primary user-facing flow calls the service
    directly from the view so a single brief request/response cycle
    doesn't need a polling UI for what's typically a few seconds of
    latency (see ContentBriefView).
    """
    try:
        trend = Trend.objects.get(id=trend_id)
    except Trend.DoesNotExist:
        logger.warning("generate_brief_task called for missing trend %s", trend_id)
        return {"trend": trend_id, "error": "not found"}

    user = get_user_model().objects.filter(id=user_id).first() if user_id else None

    try:
        brief = generate_brief(trend, user=user)
    except Exception as exc:
        logger.exception("Brief generation failed for trend %s", trend_id)
        raise self.retry(exc=exc)

    if user is not None:
        notify_user(
            user,
            NotificationType.GENERATION_COMPLETE,
            {
                "brief_id": str(brief.id),
                "trend_id": str(trend.id),
                "trend_slug": trend.slug,
                "trend_title": trend.title,
            },
        )

    return {"brief": str(brief.id), "trend": str(trend.id)}


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def generate_content_task(self, brief_id: str, content_type: str, user_id: str | None = None):
    try:
        brief = ContentBrief.objects.select_related("trend").get(id=brief_id)
    except ContentBrief.DoesNotExist:
        logger.warning("generate_content_task called for missing brief %s", brief_id)
        return {"brief": brief_id, "error": "not found"}

    user = get_user_model().objects.filter(id=user_id).first() if user_id else None

    try:
        content = generate_content(brief, content_type, user=user)
    except Exception as exc:
        logger.exception("Content generation failed for brief %s (%s)", brief_id, content_type)
        raise self.retry(exc=exc)

    if user is not None:
        notify_user(
            user,
            NotificationType.GENERATION_COMPLETE,
            {
                "content_id": str(content.id),
                "content_type": content.content_type,
                "trend_title": brief.trend.title,
            },
        )

    return {"content": str(content.id), "content_type": content.content_type}
