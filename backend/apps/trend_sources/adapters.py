"""Concrete TrendSourceAdapter implementations.

Each adapter is deliberately small: fetch raw data from the source,
map it onto RawSignalData, and nothing else. Scoring, dedup, and
everything AI-related happens later in the pipeline (apps.trends),
so a new platform only ever needs a new class here plus a Platform
row — never a change to the ingestion or analysis code.
"""

import logging
from datetime import datetime, timezone as dt_timezone

import feedparser
import requests
from django.conf import settings

from apps.trend_sources.base import RawSignalData, TrendSourceAdapter, register_adapter

logger = logging.getLogger(__name__)


@register_adapter("rss")
class RSSAdapter(TrendSourceAdapter):
    """Generic RSS/Atom feed adapter. Config: {"feed_url": "https://..."}.
    Used for the Kenyan news sources and any other feed-based source —
    adding one is a new Platform row, not new code.
    """

    def fetch_signals(self) -> list[RawSignalData]:
        feed_url = self.config.get("feed_url")
        if not feed_url:
            raise ValueError("RSSAdapter requires config['feed_url'].")

        parsed = feedparser.parse(feed_url)
        if parsed.bozo and not parsed.entries:
            raise ValueError(f"Could not parse RSS feed at {feed_url}: {parsed.bozo_exception}")

        signals = []
        for entry in parsed.entries:
            external_id = entry.get("id") or entry.get("link")
            if not external_id:
                continue

            published_at = None
            if getattr(entry, "published_parsed", None):
                published_at = datetime(*entry.published_parsed[:6], tzinfo=dt_timezone.utc)

            signals.append(
                RawSignalData(
                    external_id=external_id,
                    title=entry.get("title", "").strip(),
                    url=entry.get("link", ""),
                    summary=entry.get("summary", ""),
                    published_at=published_at,
                    raw_payload={
                        "author": entry.get("author", ""),
                        "tags": [t.term for t in entry.get("tags", [])],
                    },
                )
            )
        return signals


@register_adapter("reddit")
class RedditAdapter(TrendSourceAdapter):
    """Reddit's official OAuth API (script-app, client-credentials
    grant) — no scraping. Config: {"subreddit": "startups", "limit": 25}.
    Requires REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET in settings, from
    a "script" app registered at reddit.com/prefs/apps.
    """

    TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
    API_BASE = "https://oauth.reddit.com"

    def _get_access_token(self) -> str:
        client_id = settings.REDDIT_CLIENT_ID
        client_secret = settings.REDDIT_CLIENT_SECRET
        if not client_id or not client_secret:
            raise ValueError("Reddit OAuth is not configured (REDDIT_CLIENT_ID/SECRET missing).")

        response = requests.post(
            self.TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
            headers={"User-Agent": settings.REDDIT_USER_AGENT},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def fetch_signals(self) -> list[RawSignalData]:
        subreddit = self.config.get("subreddit")
        if not subreddit:
            raise ValueError("RedditAdapter requires config['subreddit'].")
        limit = self.config.get("limit", 25)

        token = self._get_access_token()
        response = requests.get(
            f"{self.API_BASE}/r/{subreddit}/hot",
            params={"limit": limit},
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": settings.REDDIT_USER_AGENT,
            },
            timeout=10,
        )
        response.raise_for_status()

        signals = []
        for child in response.json().get("data", {}).get("children", []):
            post = child.get("data", {})
            if not post.get("id"):
                continue
            signals.append(
                RawSignalData(
                    external_id=post["id"],
                    title=post.get("title", ""),
                    url=f"https://reddit.com{post.get('permalink', '')}",
                    summary=post.get("selftext", "")[:2000],
                    published_at=(
                        datetime.fromtimestamp(post["created_utc"], tz=dt_timezone.utc)
                        if post.get("created_utc")
                        else None
                    ),
                    raw_payload={
                        "score": post.get("score"),
                        "num_comments": post.get("num_comments"),
                        "subreddit": subreddit,
                    },
                )
            )
        return signals


@register_adapter("google-trends")
class GoogleTrendsAdapter(TrendSourceAdapter):
    """Google does not currently offer a generally-available public
    API for real-time trending searches (the official Trends API is
    limited/allowlist-access). This adapter uses `pytrends`, a
    community library that reads the same data the trends.google.com
    UI does. Treat this as an interim source: it can break if Google
    changes its frontend, and should be swapped for the official API
    the moment allowlist access is granted — the adapter interface
    means that swap touches only this file.

    Config: {"geo": "KE"}.
    """

    def fetch_signals(self) -> list[RawSignalData]:
        try:
            from pytrends.request import TrendReq
        except ImportError as exc:  # pragma: no cover
            raise ImportError("pytrends is required for the google-trends adapter.") from exc

        geo = self.config.get("geo", "KE")
        pytrends = TrendReq(hl="en-US", tz=0)

        try:
            # today_searches takes a real ISO country code (matches our
            # config's "geo" value) and hits Google's Daily Trends feed.
            # trending_searches() is deliberately not used here — it
            # takes a country *name* like 'united_states' rather than
            # an ISO code, and its underlying endpoint has been flaky
            # to the point of 404ing outright for some geos.
            titles = pytrends.today_searches(pn=geo)
        except Exception:
            logger.exception("pytrends request failed for geo=%s", geo)
            raise

        signals = []
        for title in titles:
            title = str(title).strip()
            if not title:
                continue
            signals.append(
                RawSignalData(
                    external_id=title.lower(),
                    title=title,
                    url=f"https://trends.google.com/trends/explore?q={title.replace(' ', '+')}",
                    raw_payload={"geo": geo},
                )
            )
        return signals
