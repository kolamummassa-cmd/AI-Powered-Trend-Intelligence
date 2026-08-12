import logging
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.notifications.models import NotificationType
from apps.notifications.services import notify_all_users
from apps.trend_sources.models import RawTrendSignal
from apps.trends.models import Trend, TrendStatus
from apps.trends.services import ingest_raw_signal

logger = logging.getLogger(__name__)

# A trend not reported on by any platform in this long is treated as
# cooling off; past the second threshold it's dropped from the active
# feed entirely. Arbitrary but documented choices — tune once there's
# real usage data on how long trends actually stay relevant.
EXPIRING_AFTER_DAYS = 7
EXPIRED_AFTER_DAYS = 21


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def ingest_signal(self, raw_signal_id: str):
    try:
        raw_signal = RawTrendSignal.objects.select_related("platform").get(id=raw_signal_id)
    except RawTrendSignal.DoesNotExist:
        logger.warning("ingest_signal called for missing raw signal %s", raw_signal_id)
        return {"raw_signal": raw_signal_id, "error": "not found"}

    try:
        with transaction.atomic():
            trend, is_new_trend = ingest_raw_signal(raw_signal)
    except Exception as exc:
        logger.exception("Ingestion failed for raw signal %s", raw_signal_id)
        raise self.retry(exc=exc)

    if is_new_trend:
        # Only newly-created trends get analyzed automatically — a
        # second (or fifth) platform reporting on an already-analyzed
        # trend shouldn't burn another AI call. Re-analysis is
        # available on demand (see analyze_now management command).
        #
        # Deliberately isolated from ingestion's own success/failure: a
        # missing AI_PROVIDER key or a provider outage should never
        # undo or block ingestion, which has already committed above.
        # With CELERY_TASK_ALWAYS_EAGER (local dev), .delay() runs
        # synchronously and would otherwise propagate the analysis
        # failure straight out of this task and abort poll_platform's
        # loop over the remaining signals for that platform.
        from apps.trend_analysis.tasks import analyze_trend_task

        try:
            analyze_trend_task.delay(str(trend.id))
        except Exception:
            logger.exception(
                "Auto-analysis failed to enqueue/run for trend %s — ingestion still succeeded. "
                "Backfill later with `manage.py analyze_now`.",
                trend.id,
            )

    return {
        "raw_signal": str(raw_signal_id),
        "trend": str(trend.id),
        "trend_title": trend.title,
        "is_new_trend": is_new_trend,
    }


@shared_task
def check_trend_lifecycle():
    """Daily-ish heartbeat (see CELERY_BEAT_SCHEDULE) that ages trends
    out of the feed based on how long since a platform last reported
    on them. Expiry always takes priority over "just started
    expiring" — a trend that's gone quiet for EXPIRED_AFTER_DAYS skips
    straight to expired even if it somehow never got the expiring
    notification.
    """
    now = timezone.now()
    expiring_cutoff = now - timedelta(days=EXPIRING_AFTER_DAYS)
    expired_cutoff = now - timedelta(days=EXPIRED_AFTER_DAYS)

    expired_count = (
        Trend.objects.filter(last_seen_at__lt=expired_cutoff)
        .exclude(status=TrendStatus.EXPIRED)
        .update(status=TrendStatus.EXPIRED)
    )

    newly_expiring = list(
        Trend.objects.filter(
            status=TrendStatus.ACTIVE,
            last_seen_at__lt=expiring_cutoff,
            last_seen_at__gte=expired_cutoff,
        )
    )
    for trend in newly_expiring:
        trend.status = TrendStatus.EXPIRING
        trend.save(update_fields=["status"])
        notify_all_users(
            NotificationType.EXPIRING_TREND,
            {"trend_id": str(trend.id), "trend_slug": trend.slug, "title": trend.title},
        )

    return {"marked_expired": expired_count, "marked_expiring": len(newly_expiring)}
