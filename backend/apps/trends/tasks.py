import logging

from celery import shared_task
from django.db import transaction

from apps.trend_sources.models import RawTrendSignal
from apps.trends.services import ingest_raw_signal

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def ingest_signal(self, raw_signal_id: str):
    try:
        raw_signal = RawTrendSignal.objects.select_related("platform").get(id=raw_signal_id)
    except RawTrendSignal.DoesNotExist:
        logger.warning("ingest_signal called for missing raw signal %s", raw_signal_id)
        return {"raw_signal": raw_signal_id, "error": "not found"}

    try:
        with transaction.atomic():
            trend = ingest_raw_signal(raw_signal)
    except Exception as exc:
        logger.exception("Ingestion failed for raw signal %s", raw_signal_id)
        raise self.retry(exc=exc)

    return {"raw_signal": str(raw_signal_id), "trend": str(trend.id), "trend_title": trend.title}
