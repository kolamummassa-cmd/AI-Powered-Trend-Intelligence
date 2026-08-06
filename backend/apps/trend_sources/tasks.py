import logging

from celery import shared_task
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.trend_sources.base import get_adapter
from apps.trend_sources.models import Platform, RawTrendSignal

logger = logging.getLogger(__name__)


@shared_task
def poll_due_platforms():
    """Celery Beat heartbeat (every 5 min, see CELERY_BEAT_SCHEDULE).
    Fans out to poll_platform only for platforms whose own
    poll_interval_minutes has actually elapsed, so a 60-minute-interval
    source doesn't get hit every 5 minutes just because the heartbeat is.
    """
    now = timezone.now()
    due_ids = [p.id for p in Platform.objects.filter(is_active=True) if p.is_due(now)]
    for platform_id in due_ids:
        poll_platform.delay(str(platform_id))
    return {"queued": len(due_ids)}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def poll_platform(self, platform_id: str):
    """Fetches everything currently available from one platform,
    stores each signal exactly once (unique on platform+external_id),
    and queues ingestion for whatever is new.
    """
    try:
        platform = Platform.objects.get(id=platform_id)
    except Platform.DoesNotExist:
        logger.warning("poll_platform called for missing platform %s", platform_id)
        return {"platform": platform_id, "error": "not found"}

    try:
        adapter = get_adapter(platform.adapter_key, platform.config)
        signals = adapter.fetch_signals()
    except Exception as exc:
        logger.exception("Fetching signals failed for platform %s", platform.slug)
        raise self.retry(exc=exc)

    created_count = 0
    for signal in signals:
        try:
            with transaction.atomic():
                raw_signal, created = RawTrendSignal.objects.get_or_create(
                    platform=platform,
                    external_id=signal.external_id,
                    defaults={
                        "title": signal.title,
                        "url": signal.url,
                        "summary": signal.summary,
                        "published_at": signal.published_at,
                        "raw_payload": signal.raw_payload,
                    },
                )
        except IntegrityError:
            # Lost a race with another worker polling the same platform.
            continue

        if created:
            created_count += 1
            from apps.trends.tasks import ingest_signal

            ingest_signal.delay(str(raw_signal.id))

    platform.last_polled_at = timezone.now()
    platform.save(update_fields=["last_polled_at"])

    return {"platform": platform.slug, "fetched": len(signals), "new": created_count}
