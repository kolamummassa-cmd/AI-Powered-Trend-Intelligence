from unittest.mock import MagicMock, patch

import pytest

from apps.trend_sources.adapters import GoogleTrendsAdapter, RedditAdapter, RSSAdapter
from apps.trend_sources.base import get_adapter
from apps.trend_sources.models import Platform, RawTrendSignal


class TestAdapterRegistry:
    def test_known_adapters_are_registered(self):
        for slug, cls in [
            ("rss", RSSAdapter),
            ("reddit", RedditAdapter),
            ("google-trends", GoogleTrendsAdapter),
        ]:
            adapter = get_adapter(slug, {})
            assert isinstance(adapter, cls)

    def test_unknown_adapter_raises(self):
        with pytest.raises(ValueError):
            get_adapter("not-a-real-platform")


class TestRSSAdapter:
    @patch("apps.trend_sources.adapters.feedparser.parse")
    def test_maps_feed_entries_to_signals(self, mock_parse):
        mock_parse.return_value = MagicMock(
            bozo=False,
            entries=[
                {
                    "id": "https://example.com/post-1",
                    "title": "Kenya's Fintech Boom",
                    "link": "https://example.com/post-1",
                    "summary": "A summary.",
                    "author": "Jane",
                    "tags": [],
                }
            ],
        )
        adapter = RSSAdapter({"feed_url": "https://example.com/feed"})
        signals = adapter.fetch_signals()

        assert len(signals) == 1
        assert signals[0].external_id == "https://example.com/post-1"
        assert signals[0].title == "Kenya's Fintech Boom"

    def test_requires_feed_url_in_config(self):
        adapter = RSSAdapter({})
        with pytest.raises(ValueError):
            adapter.fetch_signals()


class TestRedditAdapter:
    def test_requires_subreddit_in_config(self):
        adapter = RedditAdapter({})
        with pytest.raises(ValueError):
            adapter.fetch_signals()

    @patch("apps.trend_sources.adapters.requests.get")
    @patch("apps.trend_sources.adapters.requests.post")
    def test_maps_reddit_posts_to_signals(self, mock_post, mock_get, settings):
        settings.REDDIT_CLIENT_ID = "id"
        settings.REDDIT_CLIENT_SECRET = "secret"

        mock_post.return_value = MagicMock(
            json=lambda: {"access_token": "fake-token"}, raise_for_status=lambda: None
        )
        mock_get.return_value = MagicMock(
            json=lambda: {
                "data": {
                    "children": [
                        {
                            "data": {
                                "id": "abc123",
                                "title": "How I bootstrapped to $10k MRR",
                                "permalink": "/r/startups/abc123",
                                "selftext": "story",
                                "created_utc": 1700000000,
                                "score": 42,
                                "num_comments": 5,
                            }
                        }
                    ]
                }
            },
            raise_for_status=lambda: None,
        )

        adapter = RedditAdapter({"subreddit": "startups", "limit": 25})
        signals = adapter.fetch_signals()

        assert len(signals) == 1
        assert signals[0].external_id == "abc123"
        assert "reddit.com" in signals[0].url


class TestGoogleTrendsAdapter:
    def test_maps_today_searches_to_signals(self):
        import pandas as pd

        fake_series = pd.Series(["AI regulation", "Local elections"])

        with patch("pytrends.request.TrendReq") as mock_trend_req:
            mock_trend_req.return_value.today_searches.return_value = fake_series
            adapter = GoogleTrendsAdapter({"geo": "KE"})
            signals = adapter.fetch_signals()

        assert len(signals) == 2
        assert signals[0].title == "AI regulation"
        assert signals[0].external_id == "ai regulation"
        mock_trend_req.return_value.today_searches.assert_called_once_with(pn="KE")


@pytest.mark.django_db
class TestPollPlatformTask:
    def test_poll_platform_stores_new_signals_and_queues_ingestion(self):
        from apps.trend_sources.tasks import poll_platform

        platform = Platform.objects.create(
            name="Test RSS",
            slug="test-rss",
            adapter_key="rss",
            config={"feed_url": "https://example.com/feed"},
        )

        fake_signal = MagicMock()
        fake_signal.external_id = "post-1"
        fake_signal.title = "A trend"
        fake_signal.url = "https://example.com/post-1"
        fake_signal.summary = ""
        fake_signal.published_at = None
        fake_signal.raw_payload = {}

        with (
            patch("apps.trend_sources.tasks.get_adapter") as mock_get_adapter,
            patch("apps.trends.tasks.ingest_signal.delay") as mock_ingest_delay,
        ):
            mock_get_adapter.return_value.fetch_signals.return_value = [fake_signal]
            result = poll_platform(str(platform.id))

        assert result["new"] == 1
        assert RawTrendSignal.objects.filter(platform=platform, external_id="post-1").exists()
        mock_ingest_delay.assert_called_once()

        platform.refresh_from_db()
        assert platform.last_polled_at is not None

    def test_poll_platform_is_idempotent_on_duplicate_signals(self):
        from apps.trend_sources.tasks import poll_platform

        platform = Platform.objects.create(
            name="Test RSS",
            slug="test-rss-2",
            adapter_key="rss",
            config={"feed_url": "https://example.com/feed"},
        )
        RawTrendSignal.objects.create(platform=platform, external_id="post-1", title="Existing")

        fake_signal = MagicMock()
        fake_signal.external_id = "post-1"
        fake_signal.title = "Existing"
        fake_signal.url = ""
        fake_signal.summary = ""
        fake_signal.published_at = None
        fake_signal.raw_payload = {}

        with (
            patch("apps.trend_sources.tasks.get_adapter") as mock_get_adapter,
            patch("apps.trends.tasks.ingest_signal.delay") as mock_ingest_delay,
        ):
            mock_get_adapter.return_value.fetch_signals.return_value = [fake_signal]
            result = poll_platform(str(platform.id))

        assert result["new"] == 0
        mock_ingest_delay.assert_not_called()
        assert RawTrendSignal.objects.filter(platform=platform).count() == 1
