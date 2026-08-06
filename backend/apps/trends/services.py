import re

from django.utils import timezone

from apps.trend_sources.models import RawTrendSignal
from apps.trends.models import Trend, TrendSourceLink, TrendStatus

_NON_ALNUM = re.compile(r"[^a-z0-9\s]")
_WHITESPACE = re.compile(r"\s+")


def normalize_title(title: str) -> str:
    """Reduces a title to something comparable across platforms —
    'Kenya's AI Boom!!' and 'kenyas ai boom' should dedupe to the same
    key. Deliberately simple (no stemming/fuzzy matching) for Phase 2;
    Phase 3's AI analysis is the right place for smarter clustering of
    genuinely different headlines about the same underlying trend.
    """
    text = title.lower().strip()
    text = _NON_ALNUM.sub("", text)
    text = _WHITESPACE.sub(" ", text).strip()
    return text[:300]


def ingest_raw_signal(raw_signal: RawTrendSignal) -> Trend:
    """Turns one raw signal into either a brand-new Trend or a link on
    an existing one. Idempotent: calling this twice for the same
    raw_signal is a no-op the second time (raw_signal <-> TrendSourceLink
    is one-to-one), so retried Celery tasks can't create duplicates.
    """
    existing_link = TrendSourceLink.objects.filter(raw_signal=raw_signal).first()
    if existing_link:
        return existing_link.trend

    key = normalize_title(raw_signal.title)
    published = raw_signal.published_at or raw_signal.created_at

    trend = (
        Trend.objects.filter(dedup_key=key)
        .exclude(status=TrendStatus.EXPIRED)
        .order_by("-last_seen_at")
        .first()
    )

    if trend is None:
        trend = Trend.objects.create(
            title=raw_signal.title,
            dedup_key=key,
            summary=raw_signal.summary,
            first_detected_at=published,
            last_seen_at=published,
        )
    elif published and published > trend.last_seen_at:
        trend.last_seen_at = published
        trend.save(update_fields=["last_seen_at"])

    TrendSourceLink.objects.create(
        trend=trend,
        platform=raw_signal.platform,
        raw_signal=raw_signal,
        source_url=raw_signal.url,
    )

    raw_signal.processed_at = timezone.now()
    raw_signal.save(update_fields=["processed_at"])

    return trend
