from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.trend_sources.models import Platform, RawTrendSignal
from apps.trends.models import Category, TrendSourceLink, TrendStatus
from apps.trends.services import ingest_raw_signal, normalize_title


@pytest.fixture
def platform(db):
    return Platform.objects.create(name="Test Platform", slug="test-platform", adapter_key="rss")


def _raw_signal(platform, external_id, title, **extra):
    return RawTrendSignal.objects.create(
        platform=platform, external_id=external_id, title=title, **extra
    )


class TestNormalizeTitle:
    def test_strips_punctuation_and_case(self):
        assert normalize_title("Kenya's AI Boom!!") == normalize_title("kenyas ai boom")

    def test_collapses_whitespace(self):
        assert normalize_title("a   b\tc") == "a b c"


@pytest.mark.django_db
class TestIngestRawSignal:
    def test_creates_a_new_trend_for_a_novel_title(self, platform):
        signal = _raw_signal(platform, "1", "Kenya's Fintech Boom")
        trend = ingest_raw_signal(signal)

        assert trend.title == "Kenya's Fintech Boom"
        assert trend.first_detected_at is not None
        assert TrendSourceLink.objects.filter(trend=trend, raw_signal=signal).exists()

    def test_second_signal_with_same_normalized_title_reuses_the_trend(self, platform):
        signal_a = _raw_signal(platform, "1", "Kenya's Fintech Boom!!")
        signal_b = _raw_signal(platform, "2", "kenyas fintech boom")

        trend_a = ingest_raw_signal(signal_a)
        trend_b = ingest_raw_signal(signal_b)

        assert trend_a.id == trend_b.id
        assert trend_a.source_links.count() == 2

    def test_different_title_creates_a_separate_trend(self, platform):
        signal_a = _raw_signal(platform, "1", "Kenya's Fintech Boom")
        signal_b = _raw_signal(platform, "2", "Local Elections Update")

        trend_a = ingest_raw_signal(signal_a)
        trend_b = ingest_raw_signal(signal_b)

        assert trend_a.id != trend_b.id

    def test_expired_trend_is_not_reused(self, platform):
        signal_a = _raw_signal(platform, "1", "Old Trend")
        trend_a = ingest_raw_signal(signal_a)
        trend_a.status = TrendStatus.EXPIRED
        trend_a.save(update_fields=["status"])

        signal_b = _raw_signal(platform, "2", "Old Trend")
        trend_b = ingest_raw_signal(signal_b)

        assert trend_a.id != trend_b.id

    def test_is_idempotent_for_the_same_raw_signal(self, platform):
        signal = _raw_signal(platform, "1", "Kenya's Fintech Boom")
        trend_first = ingest_raw_signal(signal)
        trend_second = ingest_raw_signal(signal)

        assert trend_first.id == trend_second.id
        assert TrendSourceLink.objects.filter(raw_signal=signal).count() == 1

    def test_updates_last_seen_at_when_a_newer_signal_arrives(self, platform):
        now = timezone.now()
        signal_a = _raw_signal(platform, "1", "Ongoing Trend", published_at=now - timedelta(days=2))
        trend = ingest_raw_signal(signal_a)
        original_last_seen = trend.last_seen_at

        signal_b = _raw_signal(platform, "2", "ongoing trend", published_at=now)
        ingest_raw_signal(signal_b)
        trend.refresh_from_db()

        assert trend.last_seen_at > original_last_seen


@pytest.mark.django_db
class TestTrendAPI:
    def _authed_client(self):
        user = User.objects.create_user(email="creator@example.com", password="a-strong-passw0rd1")
        token = RefreshToken.for_user(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        return client

    def test_list_requires_authentication(self):
        client = APIClient()
        response = client.get("/api/v1/trends/")
        assert response.status_code == 401

    def test_list_returns_trends_with_platforms(self, platform):
        signal = _raw_signal(platform, "1", "Kenya's Fintech Boom")
        ingest_raw_signal(signal)

        client = self._authed_client()
        response = client.get("/api/v1/trends/")

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["platforms"] == ["test-platform"]

    def test_filter_by_category_slug(self, platform):
        category_a = Category.objects.create(name="Fintech")
        category_b = Category.objects.create(name="Politics")
        trend_a = ingest_raw_signal(_raw_signal(platform, "1", "Fintech News"))
        trend_a.category = category_a
        trend_a.save(update_fields=["category"])
        trend_b = ingest_raw_signal(_raw_signal(platform, "2", "Election News"))
        trend_b.category = category_b
        trend_b.save(update_fields=["category"])

        client = self._authed_client()
        response = client.get("/api/v1/trends/", {"category": "fintech"})

        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == "Fintech News"

    def test_filter_by_platform_slug(self, platform):
        other_platform = Platform.objects.create(
            name="Other", slug="other-platform", adapter_key="rss"
        )
        ingest_raw_signal(_raw_signal(platform, "1", "From test platform"))
        ingest_raw_signal(_raw_signal(other_platform, "2", "From other platform"))

        client = self._authed_client()
        response = client.get("/api/v1/trends/", {"platform": "other-platform"})

        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == "From other platform"

    def test_search_by_title(self, platform):
        ingest_raw_signal(_raw_signal(platform, "1", "Kenya's Fintech Boom"))
        ingest_raw_signal(_raw_signal(platform, "2", "Local Elections Update"))

        client = self._authed_client()
        response = client.get("/api/v1/trends/", {"search": "fintech"})

        assert response.data["count"] == 1

    def test_detail_view_includes_source_links(self, platform):
        trend = ingest_raw_signal(_raw_signal(platform, "1", "Kenya's Fintech Boom"))

        client = self._authed_client()
        response = client.get(f"/api/v1/trends/{trend.slug}/")

        assert response.status_code == 200
        assert len(response.data["source_links"]) == 1
        assert response.data["source_links"][0]["platform_slug"] == "test-platform"

    def test_detail_view_404_for_unknown_slug(self):
        client = self._authed_client()
        response = client.get("/api/v1/trends/does-not-exist/")
        assert response.status_code == 404
