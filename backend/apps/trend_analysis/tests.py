from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from ai_providers.base import TrendAnalysisResult
from apps.trend_analysis.models import TrendAnalysis
from apps.trend_analysis.services import analyze_trend
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
    def test_creates_analysis_and_updates_trend(self, mock_get_provider, trend):
        mock_provider = MagicMock()
        mock_provider.generate_trend_analysis.return_value = FAKE_RESULT
        mock_get_provider.return_value = mock_provider

        analysis = analyze_trend(trend)

        assert isinstance(analysis, TrendAnalysis)
        assert analysis.trend_score == 72
        assert TrendAnalysis.objects.filter(trend=trend).count() == 1

        trend.refresh_from_db()
        assert trend.trend_score == 72
        assert trend.opportunity_score == 65
        assert trend.confidence_score == 80
        assert trend.why_spreading == "It's spreading fast."
        assert trend.estimated_lifespan == "2-3 weeks"
        assert trend.analyzed_at is not None
        assert trend.category.name == "Fintech"

        # Audience relevance / trend intelligence, denormalized onto
        # Trend the same way the original three scores already are.
        assert trend.content_creator_score == 75
        assert trend.founder_score == 91
        assert trend.investor_score == 60
        assert trend.best_audience == "founders"
        assert trend.why_it_matters == "It matters because of the opportunity it creates."
        assert trend.what_is_happening == "A major platform just launched a new feature."
        assert trend.trend_stage == "growing"
        assert trend.suggested_content_angle == "A concrete angle a creator could use right now."

        assert analysis.content_creator_score == 75
        assert analysis.founder_score == 91
        assert analysis.investor_score == 60
        assert analysis.best_audience == "founders"

    @patch("apps.trend_analysis.services.get_ai_provider")
    def test_does_not_overwrite_an_existing_category(self, mock_get_provider, trend):
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
    def test_does_not_overwrite_an_existing_summary(self, mock_get_provider, trend):
        trend.summary = "An existing human-written summary."
        trend.save(update_fields=["summary"])

        mock_provider = MagicMock()
        mock_provider.generate_trend_analysis.return_value = FAKE_RESULT
        mock_get_provider.return_value = mock_provider

        analyze_trend(trend)
        trend.refresh_from_db()

        assert trend.summary == "An existing human-written summary."

    @patch("apps.trend_analysis.services.get_ai_provider")
    def test_reanalysis_adds_a_new_row_rather_than_replacing(self, mock_get_provider, trend):
        mock_provider = MagicMock()
        mock_provider.generate_trend_analysis.return_value = FAKE_RESULT
        mock_get_provider.return_value = mock_provider

        analyze_trend(trend)
        analyze_trend(trend)

        assert TrendAnalysis.objects.filter(trend=trend).count() == 2


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
class TestHighValueNotificationTrigger:
    @patch("apps.trend_analysis.services.get_ai_provider")
    def test_notifies_users_when_trend_newly_crosses_high_priority(self, mock_get_provider, trend):
        from apps.accounts.models import User
        from apps.notifications.models import Notification, NotificationType

        user = User.objects.create_user(email="watcher@example.com", password="a-strong-pw1")
        mock_provider = MagicMock()
        mock_provider.generate_trend_analysis.return_value = HIGH_PRIORITY_RESULT
        mock_get_provider.return_value = mock_provider

        analyze_trend(trend)

        assert Notification.objects.filter(
            user=user, type=NotificationType.NEW_HIGH_VALUE_TREND
        ).exists()

    @patch("apps.trend_analysis.services.get_ai_provider")
    def test_does_not_renotify_on_re_analysis_of_an_already_high_priority_trend(
        self, mock_get_provider, trend
    ):
        from apps.accounts.models import User
        from apps.notifications.models import Notification, NotificationType

        User.objects.create_user(email="watcher@example.com", password="a-strong-pw1")
        mock_provider = MagicMock()
        mock_provider.generate_trend_analysis.return_value = HIGH_PRIORITY_RESULT
        mock_get_provider.return_value = mock_provider

        analyze_trend(trend)
        analyze_trend(trend)

        assert Notification.objects.filter(type=NotificationType.NEW_HIGH_VALUE_TREND).count() == 1

    @patch("apps.trend_analysis.services.get_ai_provider")
    def test_does_not_notify_for_a_low_priority_trend(self, mock_get_provider, trend):
        from apps.notifications.models import Notification, NotificationType

        mock_provider = MagicMock()
        mock_provider.generate_trend_analysis.return_value = FAKE_RESULT  # below thresholds
        mock_get_provider.return_value = mock_provider

        analyze_trend(trend)

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
