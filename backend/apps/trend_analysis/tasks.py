import logging

from celery import shared_task

from ai_providers.base import AIProviderError
from apps.core.ai_jobs import _is_transient_error
from apps.trend_analysis.services import analyze_trend
from apps.trends.models import Trend

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_trend_task(self, trend_id: str):
    try:
        trend = Trend.objects.get(id=trend_id)
    except Trend.DoesNotExist:
        logger.warning("analyze_trend_task called for missing trend %s", trend_id)
        return {"trend": trend_id, "error": "not found"}

    try:
        analysis = analyze_trend(trend)
    except AIProviderError as exc:
        logger.exception("Analysis failed for trend %s", trend_id)
        if _is_transient_error(exc):
            raise self.retry(exc=exc)
        return {"trend": trend_id, "error": str(exc)}

    return {
        "trend": str(trend.id),
        "trend_score": analysis.trend_score,
        "opportunity_score": analysis.opportunity_score,
    }
