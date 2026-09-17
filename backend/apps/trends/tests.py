from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.core.models import AIJob
from apps.trend_sources.models import Platform, RawTrendSignal
from apps.trends.models import Category, Trend, TrendSourceLink, TrendStatus
from apps.trends.signal_areas import detect_signal_areas
from apps.trends.services import ingest_raw_signal, normalize_title


@pytest.fixture
def platform(db):
    return Platform.objects.create(name="Test Platform", slug="test-platform", adapter_key="rss")


def _raw_signal(platform, external_id, title, **extra):
    return RawTrendSignal.objects.create(
        platform=platform, external_id=external_id, title=title, **extra
    )


def _ingest(signal):
    """Most tests only care about the resulting Trend, not whether it
    was newly created — this unwraps ingest_raw_signal's (trend, is_new)
    tuple so those tests don't need to know about is_new at all.
    """
    trend, _ = ingest_raw_signal(signal)
    return trend


class TestNormalizeTitle:
    def test_strips_punctuation_and_case(self):
        assert normalize_title("Kenya's AI Boom!!") == normalize_title("kenyas ai boom")

    def test_collapses_whitespace(self):
        assert normalize_title("a   b\tc") == "a b c"


class TestSignalAreas:
    def test_detects_the_most_relevant_topic_labels(self):
        assert detect_signal_areas("Kenyan fintech startup raises funding") == [
            "Funding & investment",
            "Fintech & money",
        ]

    def test_falls_back_to_general_business(self):
        assert detect_signal_areas("Local company appoints a new chief executive") == [
            "Business & markets"
        ]

    def test_does_not_match_part_of_another_word(self):
        assert detect_signal_areas("Kenya's fintech boom") == [
            "Fintech & money",
            "African & Kenyan markets",
        ]


@pytest.mark.django_db
class TestIngestRawSignal:
    def test_creates_a_new_trend_for_a_novel_title(self, platform):
        signal = _raw_signal(
            platform,
            "1",
            "Kenya's Fintech Boom",
            summary="Details from the original source.",
        )
        trend, is_new = ingest_raw_signal(signal)

        assert is_new is True
        assert trend.title == "Kenya's Fintech Boom"
        assert trend.source_excerpt == "Details from the original source."
        assert trend.summary == "Details from the original source."
        assert trend.first_detected_at is not None
        assert TrendSourceLink.objects.filter(trend=trend, raw_signal=signal).exists()

    def test_second_signal_with_same_normalized_title_reuses_the_trend(self, platform):
        signal_a = _raw_signal(platform, "1", "Kenya's Fintech Boom!!")
        signal_b = _raw_signal(platform, "2", "kenyas fintech boom")

        trend_a, is_new_a = ingest_raw_signal(signal_a)
        trend_b, is_new_b = ingest_raw_signal(signal_b)

        assert trend_a.id == trend_b.id
        assert trend_a.source_links.count() == 2
        assert is_new_a is True
        assert is_new_b is False

    def test_different_title_creates_a_separate_trend(self, platform):
        signal_a = _raw_signal(platform, "1", "Kenya's Fintech Boom")
        signal_b = _raw_signal(platform, "2", "Local Elections Update")

        trend_a = _ingest(signal_a)
        trend_b = _ingest(signal_b)

        assert trend_a.id != trend_b.id

    def test_expired_trend_is_not_reused(self, platform):
        signal_a = _raw_signal(platform, "1", "Old Trend")
        trend_a = _ingest(signal_a)
        trend_a.status = TrendStatus.EXPIRED
        trend_a.save(update_fields=["status"])

        signal_b = _raw_signal(platform, "2", "Old Trend")
        trend_b, is_new_b = ingest_raw_signal(signal_b)

        assert trend_a.id != trend_b.id
        assert is_new_b is True

    def test_is_idempotent_for_the_same_raw_signal(self, platform):
        signal = _raw_signal(platform, "1", "Kenya's Fintech Boom")
        trend_first, is_new_first = ingest_raw_signal(signal)
        trend_second, is_new_second = ingest_raw_signal(signal)

        assert trend_first.id == trend_second.id
        assert is_new_first is True
        assert is_new_second is False
        assert TrendSourceLink.objects.filter(raw_signal=signal).count() == 1

    def test_updates_last_seen_at_when_a_newer_signal_arrives(self, platform):
        now = timezone.now()
        signal_a = _raw_signal(platform, "1", "Ongoing Trend", published_at=now - timedelta(days=2))
        trend = _ingest(signal_a)
        original_last_seen = trend.last_seen_at

        signal_b = _raw_signal(platform, "2", "ongoing trend", published_at=now)
        _ingest(signal_b)
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
        _ingest(signal)

        client = self._authed_client()
        response = client.get("/api/v1/trends/")

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["platforms"] == ["test-platform"]
        assert response.data["results"][0]["source_excerpt"] == ""
        assert response.data["results"][0]["signal_areas"] == [
            "Fintech & money",
            "African & Kenyan markets",
        ]

    def test_filter_by_category_slug(self, platform):
        category_a = Category.objects.create(name="Fintech")
        category_b = Category.objects.create(name="Politics")
        trend_a = _ingest(_raw_signal(platform, "1", "Fintech News"))
        trend_a.category = category_a
        trend_a.save(update_fields=["category"])
        trend_b = _ingest(_raw_signal(platform, "2", "Election News"))
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
        _ingest(_raw_signal(platform, "1", "From test platform"))
        _ingest(_raw_signal(other_platform, "2", "From other platform"))

        client = self._authed_client()
        response = client.get("/api/v1/trends/", {"platform": "other-platform"})

        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == "From other platform"

    def test_search_by_title(self, platform):
        _ingest(_raw_signal(platform, "1", "Kenya's Fintech Boom"))
        _ingest(_raw_signal(platform, "2", "Local Elections Update"))

        client = self._authed_client()
        response = client.get("/api/v1/trends/", {"search": "fintech"})

        assert response.data["count"] == 1

    def test_detail_view_includes_source_links(self, platform):
        trend = _ingest(_raw_signal(platform, "1", "Kenya's Fintech Boom"))

        client = self._authed_client()
        response = client.get(f"/api/v1/trends/{trend.slug}/")

        assert response.status_code == 200
        assert len(response.data["source_links"]) == 1
        assert response.data["source_links"][0]["platform_slug"] == "test-platform"
        assert response.data["source_links"][0]["source_title"] == "Kenya's Fintech Boom"

    def test_detail_view_404_for_unknown_slug(self):
        client = self._authed_client()
        response = client.get("/api/v1/trends/does-not-exist/")
        assert response.status_code == 404

    def test_detail_view_includes_latest_analysis(self, platform):
        from apps.trend_analysis.models import TrendAnalysis

        trend = _ingest(_raw_signal(platform, "1", "Kenya's Fintech Boom"))
        client = self._authed_client()
        user = User.objects.get(email="creator@example.com")
        TrendAnalysis.objects.create(
            trend=trend,
            created_by=user,
            business_relevance="b",
            founder_relevance="f",
            entrepreneurship_relevance="e",
            ai_relevance="a",
            trend_score=72,
            opportunity_score=65,
            confidence_score=80,
            model_used="claude",
        )

        response = client.get(f"/api/v1/trends/{trend.slug}/")

        assert response.data["latest_analysis"]["trend_score"] == 72
        assert response.data["latest_analysis"]["model_used"] == "claude"

    def test_detail_view_latest_analysis_is_none_before_analysis(self, platform):
        trend = _ingest(_raw_signal(platform, "1", "Kenya's Fintech Boom"))

        client = self._authed_client()
        response = client.get(f"/api/v1/trends/{trend.slug}/")

        assert response.data["latest_analysis"] is None

    def test_detail_view_includes_audience_relevance_and_intelligence(self, platform):
        from apps.trend_analysis.models import TrendAnalysis

        trend = _ingest(_raw_signal(platform, "1", "Kenya's Fintech Boom"))
        client = self._authed_client()
        user = User.objects.get(email="creator@example.com")
        TrendAnalysis.objects.create(
            trend=trend,
            created_by=user,
            business_relevance="b",
            founder_relevance="f",
            entrepreneurship_relevance="e",
            ai_relevance="a",
            trend_score=72,
            opportunity_score=65,
            confidence_score=80,
            content_creator_score=80,
            founder_score=95,
            investor_score=60,
            best_audience="founders",
            why_it_matters="It matters a lot.",
            what_is_happening="Something happened.",
            trend_stage="growing",
            suggested_content_angle="A concrete angle.",
            model_used="claude",
        )
        response = client.get(f"/api/v1/trends/{trend.slug}/")

        assert response.data["audience_relevance"] == {
            "content_creators": 80,
            "founders": 95,
            "investors": 60,
        }
        assert response.data["best_audience"] == "founders"
        assert response.data["why_it_matters"] == "It matters a lot."
        assert response.data["what_is_happening"] == "Something happened."
        assert response.data["trend_stage"] == "growing"
        assert response.data["suggested_content_angle"] == "A concrete angle."

    def test_detail_view_audience_relevance_is_none_before_analysis(self, platform):
        trend = _ingest(_raw_signal(platform, "1", "Kenya's Fintech Boom"))

        client = self._authed_client()
        response = client.get(f"/api/v1/trends/{trend.slug}/")

        assert response.data["audience_relevance"] is None

    def test_analysis_is_private_to_its_creator(self, platform):
        from apps.trend_analysis.models import TrendAnalysis

        trend = _ingest(
            _raw_signal(platform, "1", "Kenya's Fintech Boom", summary="Original RSS summary.")
        )
        owner = User.objects.create_user(email="owner@example.com", password="a-strong-passw0rd1")
        other = User.objects.create_user(email="other@example.com", password="a-strong-passw0rd1")
        TrendAnalysis.objects.create(
            trend=trend,
            created_by=owner,
            business_relevance="Owner analysis",
            founder_relevance="f",
            entrepreneurship_relevance="e",
            ai_relevance="a",
            trend_score=92,
            opportunity_score=88,
            confidence_score=87,
            what_is_happening="Owner's private AI result.",
            opportunity_headline="Owner's private headline",
            model_used="claude",
        )
        owner_client = APIClient()
        owner_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(owner).access_token}"
        )
        other_client = APIClient()
        other_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(other).access_token}"
        )

        owner_response = owner_client.get(f"/api/v1/trends/{trend.slug}/")
        other_response = other_client.get(f"/api/v1/trends/{trend.slug}/")

        assert owner_response.data["latest_analysis"]["trend_score"] == 92
        assert owner_response.data["opportunity_headline"] == "Owner's private headline"
        assert other_response.data["latest_analysis"] is None
        assert other_response.data["trend_score"] is None
        assert other_response.data["opportunity_headline"] == ""
        assert other_response.data["summary"] == "Original RSS summary."

    def test_filter_by_audience(self, platform):
        from apps.trend_analysis.models import TrendAnalysis

        client = self._authed_client()
        user = User.objects.get(email="creator@example.com")
        founder_trend = _ingest(_raw_signal(platform, "1", "Founder Relevant"))
        investor_trend = _ingest(_raw_signal(platform, "2", "Investor Relevant"))
        for trend, founder_score, investor_score in (
            (founder_trend, 90, 20),
            (investor_trend, 20, 90),
        ):
            TrendAnalysis.objects.create(
                trend=trend,
                created_by=user,
                business_relevance="b",
                founder_relevance="f",
                entrepreneurship_relevance="e",
                ai_relevance="a",
                trend_score=70,
                opportunity_score=70,
                confidence_score=70,
                founder_score=founder_score,
                investor_score=investor_score,
                model_used="claude",
            )
        response = client.get("/api/v1/trends/", {"audience": "investors"})

        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == "Investor Relevant"

    def test_filter_high_priority(self, platform):
        from apps.trend_analysis.models import TrendAnalysis

        client = self._authed_client()
        user = User.objects.get(email="creator@example.com")
        high = _ingest(_raw_signal(platform, "1", "High Priority Trend"))
        low = _ingest(_raw_signal(platform, "2", "Low Priority Trend"))
        for trend, trend_score, opportunity_score in ((high, 80, 75), (low, 20, 10)):
            TrendAnalysis.objects.create(
                trend=trend,
                created_by=user,
                business_relevance="b",
                founder_relevance="f",
                entrepreneurship_relevance="e",
                ai_relevance="a",
                trend_score=trend_score,
                opportunity_score=opportunity_score,
                confidence_score=70,
                model_used="claude",
            )
        response = client.get("/api/v1/trends/", {"high_priority": "true"})

        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == "High Priority Trend"

    def test_global_score_ordering_is_not_available(self, platform):
        _ingest(_raw_signal(platform, "1", "Low Score"))
        _ingest(_raw_signal(platform, "2", "High Score"))
        client = self._authed_client()
        response = client.get("/api/v1/trends/", {"ordering": "-trend_score"})
        assert response.status_code == 200


@pytest.mark.django_db
class TestIngestSignalTask:
    def test_new_trend_triggers_analysis_only_when_enabled(self, platform, settings):
        from apps.trends.tasks import ingest_signal

        signal = _raw_signal(platform, "1", "Kenya's Fintech Boom")

        settings.AI_AUTO_ANALYZE_NEW_TRENDS = True
        with patch("apps.trend_analysis.tasks.analyze_trend_task.delay") as mock_delay:
            result = ingest_signal(str(signal.id))

        assert result["is_new_trend"] is True
        mock_delay.assert_called_once()

    def test_new_trend_does_not_auto_analyze_by_default(self, platform, settings):
        from apps.trends.tasks import ingest_signal

        settings.AI_AUTO_ANALYZE_NEW_TRENDS = False
        signal = _raw_signal(platform, "1", "Kenya's Fintech Boom")

        with patch("apps.trend_analysis.tasks.analyze_trend_task.delay") as mock_delay:
            result = ingest_signal(str(signal.id))

        assert result["is_new_trend"] is True
        mock_delay.assert_not_called()

    def test_merged_trend_does_not_trigger_analysis_again(self, platform):
        from apps.trends.tasks import ingest_signal

        signal_a = _raw_signal(platform, "1", "Kenya's Fintech Boom")
        with patch("apps.trend_analysis.tasks.analyze_trend_task.delay"):
            ingest_signal(str(signal_a.id))

        signal_b = _raw_signal(platform, "2", "kenyas fintech boom")
        with patch("apps.trend_analysis.tasks.analyze_trend_task.delay") as mock_delay:
            result = ingest_signal(str(signal_b.id))

        assert result["is_new_trend"] is False
        mock_delay.assert_not_called()

    def test_analysis_failure_does_not_fail_ingestion(self, platform, settings):
        """A missing AI_PROVIDER key or provider outage should never
        undo ingestion, which has already committed by the time
        analysis is attempted (see apps.trends.tasks.ingest_signal)."""
        from apps.trends.tasks import ingest_signal

        signal = _raw_signal(platform, "1", "Kenya's Fintech Boom")
        settings.AI_AUTO_ANALYZE_NEW_TRENDS = True

        with patch(
            "apps.trend_analysis.tasks.analyze_trend_task.delay",
            side_effect=RuntimeError("boom"),
        ):
            result = ingest_signal(str(signal.id))

        assert result["is_new_trend"] is True
        assert TrendSourceLink.objects.filter(raw_signal=signal).exists()


@pytest.mark.django_db
class TestReanalyzeTrend:
    def _authed_client(self):
        user = User.objects.create_user(
            email="reanalyze@example.com", password="a-strong-pw1", is_verified=True
        )
        token = RefreshToken.for_user(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        return client

    def test_requires_authentication(self, platform):
        trend = _ingest(_raw_signal(platform, "1", "Kenya's Fintech Boom"))
        client = APIClient()
        response = client.post(f"/api/v1/trends/{trend.slug}/reanalyze/")
        assert response.status_code == 401

    def test_queues_analysis_and_returns_202(self, platform):
        trend = _ingest(_raw_signal(platform, "1", "Kenya's Fintech Boom"))
        client = self._authed_client()

        with patch("apps.trends.views.enqueue_ai_job") as mock_enqueue:
            response = client.post(f"/api/v1/trends/{trend.slug}/reanalyze/")

        assert response.status_code == 202
        assert response.data["job_type"] == AIJob.JobType.REANALYZE_TREND
        mock_enqueue.assert_called_once()

    def test_404_for_unknown_slug(self):
        client = self._authed_client()
        response = client.post("/api/v1/trends/does-not-exist/reanalyze/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestDashboardStats:
    def _authed_client(self):
        user = User.objects.create_user(email="dash@example.com", password="a-strong-passw0rd1")
        token = RefreshToken.for_user(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        return client

    def test_requires_authentication(self):
        client = APIClient()
        response = client.get("/api/v1/trends/stats/")
        assert response.status_code == 401

    def test_counts_and_platform_distribution(self, platform):
        from apps.trend_analysis.models import TrendAnalysis

        other_platform = Platform.objects.create(
            name="Other", slug="other-platform", adapter_key="rss"
        )
        high = _ingest(_raw_signal(platform, "1", "High Priority Trend"))
        _ingest(_raw_signal(other_platform, "2", "Unanalyzed Trend"))

        expired = _ingest(_raw_signal(platform, "3", "Old Trend"))
        expired.status = TrendStatus.EXPIRED
        expired.save(update_fields=["status"])

        client = self._authed_client()
        user = User.objects.get(email="dash@example.com")
        TrendAnalysis.objects.create(
            trend=high,
            created_by=user,
            business_relevance="b",
            founder_relevance="f",
            entrepreneurship_relevance="e",
            ai_relevance="a",
            trend_score=80,
            opportunity_score=75,
            confidence_score=80,
            model_used="claude",
        )
        response = client.get("/api/v1/trends/stats/")

        assert response.status_code == 200
        assert response.data["total_trends"] == 3
        assert response.data["high_priority_trends"] == 1
        assert response.data["analyzed_trends"] == 1
        assert response.data["new_today"] == 3

        slugs = {row["slug"] for row in response.data["platform_distribution"]}
        assert slugs == {"test-platform", "other-platform"}


@pytest.mark.django_db
class TestCheckTrendLifecycle:
    def test_marks_stale_active_trend_as_expiring_and_notifies(self, platform):
        from apps.notifications.models import Notification, NotificationType
        from apps.trends.tasks import EXPIRING_AFTER_DAYS, check_trend_lifecycle

        user = User.objects.create_user(email="watcher@example.com", password="a-strong-pw1")
        trend = _ingest(_raw_signal(platform, "1", "Cooling Trend"))
        trend.last_seen_at = timezone.now() - timedelta(days=EXPIRING_AFTER_DAYS + 1)
        trend.save(update_fields=["last_seen_at"])

        result = check_trend_lifecycle()

        trend.refresh_from_db()
        assert trend.status == TrendStatus.EXPIRING
        assert result["marked_expiring"] == 1
        assert Notification.objects.filter(user=user, type=NotificationType.EXPIRING_TREND).exists()

    def test_marks_very_stale_trend_as_expired_without_expiring_step(self, platform):
        from apps.trends.tasks import EXPIRED_AFTER_DAYS, check_trend_lifecycle

        trend = _ingest(_raw_signal(platform, "1", "Ancient Trend"))
        trend.last_seen_at = timezone.now() - timedelta(days=EXPIRED_AFTER_DAYS + 1)
        trend.save(update_fields=["last_seen_at"])

        result = check_trend_lifecycle()

        trend.refresh_from_db()
        assert trend.status == TrendStatus.EXPIRED
        assert result["marked_expired"] == 1

    def test_leaves_fresh_trends_alone(self, platform):
        from apps.trends.tasks import check_trend_lifecycle

        trend = _ingest(_raw_signal(platform, "1", "Fresh Trend"))

        result = check_trend_lifecycle()

        trend.refresh_from_db()
        assert trend.status == TrendStatus.ACTIVE
        assert result == {"marked_expired": 0, "marked_expiring": 0, "permanently_deleted": 0}

    def test_purges_expired_trend_after_retention_when_it_has_no_content(self, platform):
        from apps.trends.tasks import (
            EXPIRED_AFTER_DAYS,
            PURGE_EXPIRED_AFTER_DAYS,
            check_trend_lifecycle,
        )

        trend = _ingest(_raw_signal(platform, "1", "Disposable Trend"))
        trend.status = TrendStatus.EXPIRED
        trend.expired_at = timezone.now() - timedelta(days=PURGE_EXPIRED_AFTER_DAYS + 1)
        trend.last_seen_at = timezone.now() - timedelta(days=EXPIRED_AFTER_DAYS + 20)
        trend.save(update_fields=["status", "expired_at", "last_seen_at"])

        check_trend_lifecycle()

        assert not Trend.all_objects.filter(id=trend.id).exists()

    def test_keeps_expired_trend_after_retention_when_it_has_content(self, platform):
        from apps.content_studio.models import ContentBrief
        from apps.trends.tasks import PURGE_EXPIRED_AFTER_DAYS, check_trend_lifecycle

        trend = _ingest(_raw_signal(platform, "1", "Kept Trend"))
        trend.status = TrendStatus.EXPIRED
        trend.expired_at = timezone.now() - timedelta(days=PURGE_EXPIRED_AFTER_DAYS + 1)
        trend.save(update_fields=["status", "expired_at"])
        user = User.objects.create_user(
            email="brief-owner@example.com", password="a-strong-passw0rd1"
        )
        ContentBrief.objects.create(trend=trend, created_by=user)

        result = check_trend_lifecycle()

        trend.refresh_from_db()
        assert result["permanently_deleted"] == 0
        assert trend.status == TrendStatus.EXPIRED

    def test_keeps_expired_trend_marked_for_legal_retention(self, platform):
        from apps.trends.tasks import PURGE_EXPIRED_AFTER_DAYS, check_trend_lifecycle

        trend = _ingest(_raw_signal(platform, "1", "Retained Trend"))
        trend.status = TrendStatus.EXPIRED
        trend.retention_required = True
        trend.expired_at = timezone.now() - timedelta(days=PURGE_EXPIRED_AFTER_DAYS + 1)
        trend.save(update_fields=["status", "retention_required", "expired_at"])

        result = check_trend_lifecycle()

        trend.refresh_from_db()
        assert result["permanently_deleted"] == 0
        assert trend.status == TrendStatus.EXPIRED
