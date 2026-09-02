import re

from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.utils import timezone

from apps.trend_sources.models import Platform, RawTrendSignal
from apps.trends.filters import HIGH_PRIORITY_OPPORTUNITY_SCORE, HIGH_PRIORITY_TREND_SCORE
from apps.trends.models import Trend, TrendSourceLink, TrendStatus

DASHBOARD_STATS_CACHE_KEY = "trends:dashboard_stats"
DASHBOARD_STATS_CACHE_TTL = 30  # seconds — read-heavy aggregate, short TTL keeps it fresh enough

_NON_ALNUM = re.compile(r"[^a-z0-9\s]")
_WHITESPACE = re.compile(r"\s+")
_TOKEN_RE = re.compile(r"[a-z0-9]{3,}")


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


def _title_similarity(left: str, right: str) -> float:
    """Token-set similarity catches headline rewrites without over-merging short titles."""
    left_tokens = set(_TOKEN_RE.findall(left))
    right_tokens = set(_TOKEN_RE.findall(right))
    if len(left_tokens) < 3 or len(right_tokens) < 3:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _find_matching_trend(key: str):
    exact = Trend.objects.filter(active_dedup_key=key).first()
    if exact:
        return exact
    candidates = Trend.objects.exclude(status=TrendStatus.EXPIRED).only(
        "id", "dedup_key", "last_seen_at"
    ).order_by("-last_seen_at")[:250]
    return next((trend for trend in candidates if _title_similarity(key, trend.dedup_key) >= 0.72), None)


def _source_relevance(trend_title: str, signal_title: str) -> int:
    similarity = _title_similarity(normalize_title(trend_title), normalize_title(signal_title))
    return max(20, min(100, round(similarity * 100)))


def ingest_raw_signal(raw_signal: RawTrendSignal) -> tuple[Trend, bool]:
    """Turns one raw signal into either a brand-new Trend or a link on
    an existing one. Idempotent: calling this twice for the same
    raw_signal is a no-op the second time (raw_signal <-> TrendSourceLink
    is one-to-one), so retried Celery tasks can't create duplicates.

    Returns (trend, is_new_trend) — the caller (apps.trends.tasks)
    uses is_new_trend to decide whether to kick off AI analysis: a
    trend already being analyzed shouldn't be re-analyzed just because
    a second platform started reporting on it too.
    """
    existing_link = TrendSourceLink.objects.filter(raw_signal=raw_signal).first()
    if existing_link:
        return existing_link.trend, False

    key = normalize_title(raw_signal.title)
    published = raw_signal.published_at or raw_signal.created_at

    with transaction.atomic():
        # Recheck while locked: a Celery retry or another worker may have
        # connected this signal after the cheap preflight above.
        existing_link = TrendSourceLink.objects.select_related("trend").filter(raw_signal=raw_signal).first()
        if existing_link:
            return existing_link.trend, False

        trend = _find_matching_trend(key)
        is_new_trend = trend is None
        if is_new_trend:
            try:
                with transaction.atomic():
                    trend = Trend.objects.create(
                        title=raw_signal.title,
                        dedup_key=key,
                        active_dedup_key=key,
                        summary=raw_signal.summary,
                        first_detected_at=published,
                        last_seen_at=published,
                    )
            except IntegrityError:
                # The unique key is the final concurrency guard for identical titles.
                trend = Trend.objects.get(active_dedup_key=key)
                is_new_trend = False
        elif published and published > trend.last_seen_at:
            trend.last_seen_at = published
            trend.save(update_fields=["last_seen_at"])

        TrendSourceLink.objects.create(
            trend=trend,
            platform=raw_signal.platform,
            raw_signal=raw_signal,
            source_url=raw_signal.url,
            relevance_score=_source_relevance(trend.title, raw_signal.title),
        )

        raw_signal.processed_at = timezone.now()
        raw_signal.save(update_fields=["processed_at"])

    return trend, is_new_trend


def get_dashboard_stats() -> dict:
    """Aggregate counters for the Phase 4 dashboard. Kept as a single
    service function (rather than inline in the view) so the same
    numbers can later be reused by the analytics screen or a
    notification threshold check without duplicating queries.

    Cached for DASHBOARD_STATS_CACHE_TTL seconds — this runs several
    COUNT queries over the whole Trend table and is hit by every
    dashboard page load, so a short cache window trades a small amount
    of staleness for a lot fewer repeated aggregate queries.
    """
    cached = cache.get(DASHBOARD_STATS_CACHE_KEY)
    if cached is not None:
        return cached

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    trends = Trend.objects.all()
    platform_distribution = (
        Platform.objects.filter(is_active=True)
        .annotate(trend_count=Count("trend_links__trend", distinct=True))
        .order_by("-trend_count")
        .values("slug", "name", "trend_count", "kuzana_priority_weight")
    )

    stats = {
        "total_trends": trends.count(),
        "active_trends": trends.filter(status=TrendStatus.ACTIVE).count(),
        "expiring_trends": trends.filter(status=TrendStatus.EXPIRING).count(),
        "new_today": trends.filter(first_detected_at__gte=today_start).count(),
        "high_priority_trends": trends.filter(
            trend_score__gte=HIGH_PRIORITY_TREND_SCORE,
            opportunity_score__gte=HIGH_PRIORITY_OPPORTUNITY_SCORE,
        ).count(),
        "analyzed_trends": trends.filter(analyzed_at__isnull=False).count(),
        "platform_distribution": list(platform_distribution),
    }
    cache.set(DASHBOARD_STATS_CACHE_KEY, stats, DASHBOARD_STATS_CACHE_TTL)
    return stats
