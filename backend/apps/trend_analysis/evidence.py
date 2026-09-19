"""Deterministic evidence collection and scoring for a trend analysis.

The AI explains a trend, but it must not be the sole authority on whether the
underlying evidence is strong. This module calculates that part from observable
signals: recent source count, source credibility, freshness, source diversity,
and optional live-news corroboration.
"""

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone as dt_timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from ai_providers.base import SourceSnippet
from apps.trends.models import Trend

logger = logging.getLogger(__name__)

SERPER_NEWS_URL = "https://google.serper.dev/news"
MAX_INTERNAL_CONTEXT_SOURCES = 5
MAX_EXTERNAL_CONTEXT_SOURCES = 3


@dataclass(frozen=True)
class EvidenceResult:
    score: int
    feed_source_count: int
    verified_source_count: int
    summary: str
    external_sources: list[SourceSnippet] = field(default_factory=list)


def _freshness_score(published_at: datetime | None, now: datetime) -> int:
    """Turn an observed source age into a transparent 0-100 freshness value."""
    if published_at is None:
        return 0
    age_hours = max(0, (now - published_at).total_seconds() / 3600)
    if age_hours <= 24:
        return 100
    if age_hours <= 72:
        return 85
    if age_hours <= 168:
        return 50
    return 10


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def _parse_search_date(value: object, now: datetime) -> datetime | None:
    """Parse common Serper news date shapes without accepting undated results."""
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    relative = re.fullmatch(r"(\d+)\s+(minute|hour|day)s?\s+ago", text, re.IGNORECASE)
    if relative:
        amount, unit = relative.groups()
        return now - timedelta(**{f"{unit}s": int(amount)})
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(text)
        except (TypeError, ValueError):
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_timezone.utc)
    return parsed.astimezone(dt_timezone.utc)


def _fetch_live_news(title: str, now: datetime) -> list[SourceSnippet]:
    """Return recent independent news corroboration when explicitly configured.

    Network/API failures intentionally result in no external evidence rather
    than blocking a user's analysis. The resulting score remains truthful: it
    simply contains no web-corroboration component.
    """
    if not settings.SERPER_API_KEY:
        return []

    cache_key = f"trend-live-news:{hashlib.sha256(title.encode()).hexdigest()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return [SourceSnippet(**source) for source in cached]

    try:
        response = requests.post(
            SERPER_NEWS_URL,
            headers={"X-API-KEY": settings.SERPER_API_KEY, "Content-Type": "application/json"},
            json={"q": title, "num": 10},
            timeout=8,
        )
        response.raise_for_status()
        items = response.json().get("news", [])
    except (requests.RequestException, ValueError) as exc:
        logger.warning("Live news verification failed for trend %r: %s", title, exc)
        return []

    cutoff = now - timedelta(hours=settings.WEB_VERIFICATION_MAX_AGE_HOURS)
    sources: list[SourceSnippet] = []
    domains: set[str] = set()
    for item in items:
        published_at = _parse_search_date(item.get("date"), now)
        url = item.get("link", "")
        domain = _domain(url)
        if not published_at or published_at < cutoff or not domain or domain in domains:
            continue
        domains.add(domain)
        sources.append(
            SourceSnippet(
                platform=item.get("source", domain),
                title=item.get("title", "").strip(),
                summary=item.get("snippet", "").strip(),
                url=url,
                published_at=published_at,
                # Search results are corroboration, not a replacement for
                # editorially configured primary sources.
                credibility_weight=65,
                kuzana_priority_weight=50,
                relevance_score=70,
            )
        )
        if len(sources) == MAX_EXTERNAL_CONTEXT_SOURCES:
            break

    cache.set(
        cache_key,
        [source.__dict__ for source in sources],
        settings.WEB_VERIFICATION_CACHE_TTL_SECONDS,
    )
    return sources


def verify_trend_evidence(trend: Trend) -> EvidenceResult:
    """Collect deterministic evidence facts before the AI is asked to interpret them.

    Score formula (0-100): 30 source volume, 25 configured source credibility,
    25 freshness, 10 platform diversity, 10 live-web corroboration.
    """
    now = timezone.now()
    all_links = list(
        trend.source_links.select_related("platform", "raw_signal").order_by("-created_at")
    )
    # Undated material is not proof that a trend is current. It may still be
    # visible as a source record, but it earns no deterministic evidence credit.
    links = [link for link in all_links if link.raw_signal.published_at]
    feed_source_count = len(links)
    external_sources = _fetch_live_news(trend.title, now)
    verified_source_count = len(external_sources)

    if not links:
        return EvidenceResult(
            score=0,
            feed_source_count=0,
            verified_source_count=verified_source_count,
            summary=(
                "No dated feed evidence is available for this trend. "
                f"{verified_source_count} recent web corroboration"
                f"{'s' if verified_source_count != 1 else ''} were found."
            ),
            external_sources=external_sources,
        )

    volume_component = 30 * min(feed_source_count, 4) / 4
    credibility_component = 25 * (
        sum(link.platform.credibility_weight for link in links) / feed_source_count
    ) / 100
    average_freshness = (
        sum(_freshness_score(link.raw_signal.published_at, now) for link in links)
        / feed_source_count
    )
    freshness_component = 25 * average_freshness / 100
    diversity_component = 10 * min(len({link.platform_id for link in links}), 3) / 3
    corroboration_component = 10 * min(verified_source_count, 3) / 3
    score = round(
        volume_component
        + credibility_component
        + freshness_component
        + diversity_component
        + corroboration_component
    )

    web_status = (
        f"{verified_source_count} recent independent web corroboration"
        f"{'s' if verified_source_count != 1 else ''}"
        if settings.SERPER_API_KEY
        else "live web corroboration is not configured"
    )
    return EvidenceResult(
        score=max(0, min(100, score)),
        feed_source_count=feed_source_count,
        verified_source_count=verified_source_count,
        summary=(
            f"Calculated from {feed_source_count} dated feed source"
            f"{'s' if feed_source_count != 1 else ''}, configured source credibility, freshness, "
            f"platform diversity, and {web_status}."
        ),
        external_sources=external_sources,
    )
