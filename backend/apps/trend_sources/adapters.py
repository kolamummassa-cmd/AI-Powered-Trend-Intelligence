"""Concrete TrendSourceAdapter implementations.

Each adapter is deliberately small: fetch raw data from the source,
map it onto RawSignalData, and nothing else. Scoring, dedup, and
everything AI-related happens later in the pipeline (apps.trends),
so a new platform only ever needs a new class here plus a Platform
row — never a change to the ingestion or analysis code.
"""

import logging
import re
from datetime import datetime, timezone as dt_timezone

import feedparser
import requests
from django.conf import settings
from django.utils.html import strip_tags

from apps.trend_sources.base import RawSignalData, TrendSourceAdapter, register_adapter

logger = logging.getLogger(__name__)

# hnrss.org (and similar feed generators) wrap every entry's description in
# "Article URL: <a href=...>...</a>" / "Comments URL: ..." / "Points: N" /
# "# Comments: N" boilerplate — it's link metadata, not an actual summary of
# the article. After stripping HTML tags, a summary that's *just* this
# boilerplate is worse than no summary at all, so it gets dropped entirely
# instead of shown as-is.
_LINK_METADATA_BOILERPLATE_RE = re.compile(
    r"^Article URL:.*Comments URL:.*Points:\s*\d+.*#\s*Comments:\s*\d+\s*$",
    re.DOTALL,
)


def _clean_summary(raw_summary: str) -> str:
    """Strips HTML tags from a feed entry's description and collapses the
    remaining whitespace. Different feeds put wildly different content in
    this field — some plain text, some full HTML with embedded links —
    so every RSS-sourced summary goes through this before being stored.
    """
    text = strip_tags(raw_summary or "").strip()
    text = re.sub(r"\s+", " ", text)
    if _LINK_METADATA_BOILERPLATE_RE.match(text):
        return ""
    return text


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
                    summary=_clean_summary(entry.get("summary", "")),
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


@register_adapter("youtube-shorts")
class YouTubeShortsAdapter(TrendSourceAdapter):
    """YouTube Data API v3 (`search.list`) — a genuinely public,
    officially supported API; only an API key is required (no ToS
    issue, unlike a scraping approach). Config: {"query": "ai tools",
    "region_code": "US", "max_results": 25}. `query` is required —
    the API has no "trending Shorts" firehose, only search, so this
    adapter tracks specific topics/keywords rather than discovering
    new ones on its own.
    """

    SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

    def fetch_signals(self) -> list[RawSignalData]:
        query = self.config.get("query")
        if not query:
            raise ValueError("YouTubeShortsAdapter requires config['query'].")
        if not settings.YOUTUBE_API_KEY:
            raise ValueError("YOUTUBE_API_KEY is not configured.")

        response = requests.get(
            self.SEARCH_URL,
            params={
                "key": settings.YOUTUBE_API_KEY,
                "part": "snippet",
                "type": "video",
                "videoDuration": "short",  # YouTube's own "short" bucket (<4 min), the
                # closest server-side filter to Shorts the Search API exposes.
                "order": "viewCount",
                "q": query,
                "regionCode": self.config.get("region_code", "US"),
                "maxResults": self.config.get("max_results", 25),
            },
            timeout=10,
        )
        response.raise_for_status()

        signals = []
        for item in response.json().get("items", []):
            video_id = item.get("id", {}).get("videoId")
            snippet = item.get("snippet", {})
            if not video_id:
                continue
            signals.append(
                RawSignalData(
                    external_id=video_id,
                    title=snippet.get("title", ""),
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    summary=snippet.get("description", "")[:2000],
                    published_at=_parse_iso8601(snippet.get("publishedAt")),
                    raw_payload={"channel": snippet.get("channelTitle", ""), "query": query},
                )
            )
        return signals


@register_adapter("x")
class XAdapter(TrendSourceAdapter):
    """X (Twitter) API v2 recent search (`GET /2/tweets/search/recent`)
    — officially supported, App-only Bearer token auth. Requires at
    least the Basic API tier. X removed general trending-topics access
    for most tiers, so — like YouTube above — this tracks a configured
    query/hashtag rather than discovering trends on its own.
    Config: {"query": "#AItools", "max_results": 25}.
    """

    SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"

    def fetch_signals(self) -> list[RawSignalData]:
        query = self.config.get("query")
        if not query:
            raise ValueError("XAdapter requires config['query'].")
        if not settings.X_BEARER_TOKEN:
            raise ValueError("X_BEARER_TOKEN is not configured.")

        response = requests.get(
            self.SEARCH_URL,
            headers={"Authorization": f"Bearer {settings.X_BEARER_TOKEN}"},
            params={
                "query": query,
                "max_results": max(10, min(self.config.get("max_results", 25), 100)),
                "tweet.fields": "created_at,public_metrics",
            },
            timeout=10,
        )
        response.raise_for_status()

        signals = []
        for tweet in response.json().get("data", []):
            tweet_id = tweet.get("id")
            if not tweet_id:
                continue
            signals.append(
                RawSignalData(
                    external_id=tweet_id,
                    title=tweet.get("text", "")[:500],
                    url=f"https://x.com/i/web/status/{tweet_id}",
                    published_at=_parse_iso8601(tweet.get("created_at")),
                    raw_payload={"query": query, "metrics": tweet.get("public_metrics", {})},
                )
            )
        return signals


@register_adapter("tiktok")
class TikTokAdapter(TrendSourceAdapter):
    """TikTok's Research API (`POST /v2/research/video/query/`) — the
    only officially sanctioned way to query TikTok video data
    programmatically. Unlike the other adapters here, access is by
    application review (academic/nonprofit research use cases,
    reference: developers.tiktok.com/products/research-api) rather
    than a simple API key signup — flag this to Kolamu as a real
    dependency outside our own timeline if TikTok coverage is needed
    for the pitch. No scraping fallback is implemented; TikTok's ToS
    explicitly prohibits it.

    Config: {"query": "ai tools", "region_code": "US", "max_count": 25}.
    """

    QUERY_URL = "https://open.tiktokapis.com/v2/research/video/query/"

    def fetch_signals(self) -> list[RawSignalData]:
        query = self.config.get("query")
        if not query:
            raise ValueError("TikTokAdapter requires config['query'].")
        if not settings.TIKTOK_RESEARCH_TOKEN:
            raise ValueError("TIKTOK_RESEARCH_TOKEN is not configured.")

        response = requests.post(
            self.QUERY_URL,
            headers={
                "Authorization": f"Bearer {settings.TIKTOK_RESEARCH_TOKEN}",
                "Content-Type": "application/json",
            },
            params={"fields": "id,video_description,create_time,share_count,like_count"},
            json={
                "query": {
                    "and": [
                        {
                            "operation": "IN",
                            "field_name": "region_code",
                            "field_values": [self.config.get("region_code", "US")],
                        },
                        {"operation": "EQ", "field_name": "keyword", "field_values": [query]},
                    ]
                },
                "max_count": self.config.get("max_count", 25),
            },
            timeout=15,
        )
        response.raise_for_status()

        signals = []
        for video in response.json().get("data", {}).get("videos", []):
            video_id = video.get("id")
            if not video_id:
                continue
            signals.append(
                RawSignalData(
                    external_id=str(video_id),
                    title=(video.get("video_description") or "")[:500],
                    url=f"https://www.tiktok.com/@_/video/{video_id}",
                    published_at=(
                        datetime.fromtimestamp(video["create_time"], tz=dt_timezone.utc)
                        if video.get("create_time")
                        else None
                    ),
                    raw_payload={
                        "query": query,
                        "share_count": video.get("share_count"),
                        "like_count": video.get("like_count"),
                    },
                )
            )
        return signals


@register_adapter("instagram")
class InstagramAdapter(TrendSourceAdapter):
    """Instagram Graph API hashtag search (`ig_hashtag_search` +
    `recent_media`) — the only officially sanctioned way to discover
    public content by topic; there is no "trending Reels" firehose.
    Requires a Facebook App, an Instagram Business/Creator account
    (INSTAGRAM_BUSINESS_ACCOUNT_ID) linked to it, and a long-lived
    access token — and hashtag search is quota-limited to 30 distinct
    hashtags per Instagram Business Account per 7 days, so `hashtag`
    should be chosen deliberately per Platform row rather than swapped
    frequently. Config: {"hashtag": "aitools"}.
    """

    API_BASE = "https://graph.facebook.com/v19.0"

    def fetch_signals(self) -> list[RawSignalData]:
        hashtag = self.config.get("hashtag")
        if not hashtag:
            raise ValueError("InstagramAdapter requires config['hashtag'].")
        if not settings.INSTAGRAM_ACCESS_TOKEN or not settings.INSTAGRAM_BUSINESS_ACCOUNT_ID:
            raise ValueError(
                "INSTAGRAM_ACCESS_TOKEN / INSTAGRAM_BUSINESS_ACCOUNT_ID are not configured."
            )

        search_response = requests.get(
            f"{self.API_BASE}/ig_hashtag_search",
            params={
                "user_id": settings.INSTAGRAM_BUSINESS_ACCOUNT_ID,
                "q": hashtag,
                "access_token": settings.INSTAGRAM_ACCESS_TOKEN,
            },
            timeout=10,
        )
        search_response.raise_for_status()
        hashtag_results = search_response.json().get("data", [])
        if not hashtag_results:
            return []
        hashtag_id = hashtag_results[0]["id"]

        media_response = requests.get(
            f"{self.API_BASE}/{hashtag_id}/recent_media",
            params={
                "user_id": settings.INSTAGRAM_BUSINESS_ACCOUNT_ID,
                "fields": "id,caption,permalink,timestamp,like_count,comments_count",
                "access_token": settings.INSTAGRAM_ACCESS_TOKEN,
            },
            timeout=10,
        )
        media_response.raise_for_status()

        signals = []
        for media in media_response.json().get("data", []):
            media_id = media.get("id")
            if not media_id:
                continue
            signals.append(
                RawSignalData(
                    external_id=media_id,
                    title=(media.get("caption") or f"#{hashtag} post")[:500],
                    url=media.get("permalink", ""),
                    published_at=_parse_iso8601(media.get("timestamp")),
                    raw_payload={
                        "hashtag": hashtag,
                        "like_count": media.get("like_count"),
                        "comments_count": media.get("comments_count"),
                    },
                )
            )
        return signals


def _parse_iso8601(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
