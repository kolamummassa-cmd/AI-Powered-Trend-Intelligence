from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings
from django.utils import timezone

from ai_providers.base import TrendAnalysisResult
from apps.trend_analysis.models import TrendAnalysis
from apps.trend_analysis.services import analyze_trend
from apps.trend_analysis.evidence import verify_trend_evidence
from apps.trend_sources.models import Platform, RawTrendSignal
from apps.trends.models import Category, Trend, TrendSourceLink

FAKE_RESULT = TrendAnalysisResult(
    business_relevance="Businesses should care.",
    founder_relevance="Founders should care.",
    entrepreneurship_relevance="There's an opportunity.",
    ai_relevance="Not directly AI-related.",
    why_spreading="It's spreading fast.",
    estimated_lifespan="2-3 weeks",
    trend_score=72,
    opportunity_score=65,
    confidence_score=80,
    content_creator_score=75,
    founder_score=91,
    investor_score=60,
    best_audience="founders",
    why_it_matters="It matters because of the opportunity it creates.",
    what_is_happening="A major platform just launched a new feature.",
    trend_stage="growing",
    suggested_content_angle="A concrete angle a creator could use right now.",
    summary="A neutral summary.",
    category_suggestion="Fintech",
    opportunity_headline="Kenya's fintech financing gap is a founder opportunity",
    founder_hook="Could your product remove the financing friction this trend exposes?",
    investor_hook="Which financing infrastructure gap is this trend making more visible?",
    creator_hook="Explain the practical founder lesson behind this financing story.",
)


@pytest.fixture
def trend(db):
    platform = Platform.objects.create(
        name="Test Platform", slug="test-platform", adapter_key="rss"
    )
    now = timezone.now()
    trend = Trend.objects.create(
        title="Kenya's Fintech Boom",
        dedup_key="kenyas fintech boom",
        first_detected_at=now,
        last_seen_at=now,
    )
    raw_signal = RawTrendSignal.objects.create(
        platform=platform, external_id="1", title="Kenya's Fintech Boom", summary="Details here."
    )
    TrendSourceLink.objects.create(
        trend=trend, platform=platform, raw_signal=raw_signal, source_url="https://example.com"
    )
    return trend


@pytest.mark.django_db
class TestAnalyzeTrend:
    @patch("apps.trend_analysis.services.get_ai_provider")
    def test_creates_private_analysis_without_updating_the_shared_trend(
        self, mock_get_provider, trend
    ):
        from apps.accounts.models import User

        user = User.objects.create_user(email="owner@example.com", password="a-strong-passw0rd1")
        mock_provider = MagicMock()
        mock_provider.generate_trend_analysis.return_value = FAKE_RESULT
        mock_get_provider.return_value = mock_provider

        analysis = analyze_trend(trend, user=user)

        assert isinstance(analysis, TrendAnalysis)
        assert analysis.created_by == user
        assert analysis.trend_score == 72
        assert analysis.summary == "A neutral summary."
        assert analysis.why_spreading == "It's spreading fast."
        assert TrendAnalysis.objects.filter(trend=trend).count() == 1

        trend.refresh_from_db()
        assert trend.trend_score is None
        assert trend.opportunity_score is None
        assert trend.confidence_score is None
        assert trend.why_spreading == ""
        assert trend.estimated_lifespan == ""
        assert trend.analyzed_at is None
        assert trend.category is None

        # The RSS/source record stays unchanged; all intelligence lives on
        # the creator-owned analysis row.
        assert trend.content_creator_score is None
        assert trend.founder_score is None
        assert trend.investor_score is None
        assert trend.source_excerpt == ""
        assert trend.summary == ""

        assert analysis.content_creator_score == 75
        assert analysis.founder_score == 91
        assert analysis.investor_score == 60
        assert analysis.best_audience == "founders"
        assert analysis.creator_hook.startswith("Explain the practical")
        assert analysis.evidence_score >= 0
        assert "No dated feed evidence" in analysis.evidence_summary

    @patch("apps.trend_analysis.services.get_ai_provider")
    def test_hides_editorial_copy_when_confidence_is_too_low(self, mock_get_provider, trend):
        weak_result = TrendAnalysisResult(**{**FAKE_RESULT.__dict__, "confidence_score": 50})
        mock_provider = MagicMock()
        mock_provider.generate_trend_analysis.return_value = weak_result
        mock_get_provider.return_value = mock_provider

        analysis = analyze_trend(trend)
        assert analysis.opportunity_headline == ""

    @patch("apps.trend_analysis.services.get_ai_provider")
    def test_does_not_change_an_existing_category(self, mock_get_provider, trend):
        existing_category = Category.objects.create(name="Existing Category")
        trend.category = existing_category
        trend.save(update_fields=["category"])

        mock_provider = MagicMock()
        mock_provider.generate_trend_analysis.return_value = FAKE_RESULT
        mock_get_provider.return_value = mock_provider

        analyze_trend(trend)
        trend.refresh_from_db()

        assert trend.category_id == existing_category.id

    @patch("apps.trend_analysis.services.get_ai_provider")
    def test_preserves_shared_source_summary(self, mock_get_provider, trend):
        trend.summary = "An existing human-written summary."
        trend.source_excerpt = "The source's original paragraph."
        trend.save(update_fields=["summary", "source_excerpt"])

        mock_provider = MagicMock()
        mock_provider.generate_trend_analysis.return_value = FAKE_RESULT
        mock_get_provider.return_value = mock_provider

        analyze_trend(trend)
        trend.refresh_from_db()

        assert trend.source_excerpt == "The source's original paragraph."
        assert trend.summary == "An existing human-written summary."

    @patch("apps.trend_analysis.services.get_ai_provider")
    def test_reanalysis_adds_a_new_row_rather_than_replacing(self, mock_get_provider, trend):
        mock_provider = MagicMock()
        mock_provider.generate_trend_analysis.return_value = FAKE_RESULT
        mock_get_provider.return_value = mock_provider

        analyze_trend(trend)
        analyze_trend(trend)

        assert TrendAnalysis.objects.filter(trend=trend).count() == 2


@pytest.mark.django_db
class TestEvidenceVerification:
    @override_settings(SERPER_API_KEY="")
    def test_scores_recent_credible_diverse_feed_evidence_deterministically(self, trend):
        now = timezone.now()
        first_link = trend.source_links.first()
        first_link.raw_signal.published_at = now - timedelta(hours=4)
        first_link.raw_signal.save(update_fields=["published_at"])
        first_link.platform.credibility_weight = 100
        first_link.platform.save(update_fields=["credibility_weight"])

        second_platform = Platform.objects.create(
            name="Second Source", slug="second-source", adapter_key="rss", credibility_weight=100
        )
        second_signal = RawTrendSignal.objects.create(
            platform=second_platform,
            external_id="two",
            title=trend.title,
            published_at=now - timedelta(hours=6),
        )
        TrendSourceLink.objects.create(
            trend=trend,
            platform=second_platform,
            raw_signal=second_signal,
            source_url="https://second.example.com/story",
            relevance_score=100,
        )

        result = verify_trend_evidence(trend)

        assert result.feed_source_count == 2
        assert result.verified_source_count == 0
        assert result.score == 72
        assert "live web corroboration is not configured" in result.summary

    @override_settings(SERPER_API_KEY="test-key", WEB_VERIFICATION_MAX_AGE_HOURS=72)
    @patch("apps.trend_analysis.evidence.requests.post")
    def test_counts_only_recent_distinct_web_results(self, mock_post, trend):
        mock_post.return_value = MagicMock(
            raise_for_status=lambda: None,
            json=lambda: {
                "news": [
                    {
                        "title": "Independent report",
                        "snippet": "Recent corroboration.",
                        "link": "https://news.example.com/report",
                        "source": "Example News",
                        "date": "2 hours ago",
                    },
                    {
                        "title": "Duplicate publisher",
                        "snippet": "Should not count twice.",
                        "link": "https://news.example.com/another-report",
                        "source": "Example News",
                        "date": "1 hour ago",
                    },
                    {
                        "title": "Old report",
                        "snippet": "Too old.",
                        "link": "https://old.example.com/report",
                        "source": "Old News",
                        "date": "4 days ago",
                    },
                ]
            },
        )

        result = verify_trend_evidence(trend)

        assert result.verified_source_count == 1
        assert len(result.external_sources) == 1
        assert result.external_sources[0].platform == "Example News"


HIGH_PRIORITY_RESULT = TrendAnalysisResult(
    business_relevance="Businesses should care.",
    founder_relevance="Founders should care.",
    entrepreneurship_relevance="There's an opportunity.",
    ai_relevance="Not directly AI-related.",
    why_spreading="It's spreading fast.",
    estimated_lifespan="2-3 weeks",
    trend_score=85,
    opportunity_score=80,
    confidence_score=90,
)


@pytest.mark.django_db
class TestPrivateAnalysisNotifications:
    @patch("apps.trend_analysis.services.get_ai_provider")
    def test_does_not_notify_other_users_about_a_private_analysis(self, mock_get_provider, trend):
        from apps.accounts.models import User
        from apps.notifications.models import Notification, NotificationType

        owner = User.objects.create_user(email="owner@example.com", password="a-strong-pw1")
        User.objects.create_user(email="watcher@example.com", password="a-strong-pw1")
        mock_provider = MagicMock()
        mock_provider.generate_trend_analysis.return_value = HIGH_PRIORITY_RESULT
        mock_get_provider.return_value = mock_provider

        analyze_trend(trend, user=owner)

        assert not Notification.objects.filter(type=NotificationType.NEW_HIGH_VALUE_TREND).exists()


@pytest.mark.django_db
class TestAnalyzeTrendTask:
    @patch("apps.trend_analysis.tasks.analyze_trend")
    def test_returns_scores_on_success(self, mock_analyze, trend):
        from apps.trend_analysis.tasks import analyze_trend_task

        mock_analyze.return_value = MagicMock(trend_score=72, opportunity_score=65)
        result = analyze_trend_task(str(trend.id))

        assert result["trend_score"] == 72
        assert result["opportunity_score"] == 65

    def test_missing_trend_returns_error_without_raising(self):
        from apps.trend_analysis.tasks import analyze_trend_task
        import uuid

        result = analyze_trend_task(str(uuid.uuid4()))
        assert result["error"] == "not found"
