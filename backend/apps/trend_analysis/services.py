from django.utils import timezone

from ai_providers import get_ai_provider
from ai_providers.base import SourceSnippet, TrendAnalysisContext
from apps.notifications.models import NotificationType
from apps.notifications.services import notify_all_users
from apps.trend_analysis.models import TrendAnalysis
from apps.trends.filters import HIGH_PRIORITY_OPPORTUNITY_SCORE, HIGH_PRIORITY_TREND_SCORE
from apps.trends.models import Category, Trend


OPPORTUNITY_HEADLINE_MIN_KUZANA_SCORE = 70
OPPORTUNITY_HEADLINE_MIN_CONFIDENCE_SCORE = 60


def _should_surface_opportunity_copy(result) -> bool:
    """Only turn a source headline into editorial copy when the model has
    both a strong Kuzana connection and enough evidence confidence.
    """
    return (
        result.kuzana_relevance_score >= OPPORTUNITY_HEADLINE_MIN_KUZANA_SCORE
        and result.confidence_score >= OPPORTUNITY_HEADLINE_MIN_CONFIDENCE_SCORE
        and bool(result.opportunity_headline)
    )


def build_action_summary(trend: Trend) -> str:
    """A deterministic, concise decision aid—never an untraceable extra AI claim."""
    source_count = trend.source_links.count()
    confidence = trend.confidence_score or 0
    opportunity = trend.opportunity_score or 0
    urgency = "Act now" if trend.trend_stage in {"emerging", "growing"} else "Monitor closely"
    return (
        f"{urgency}: opportunity is {opportunity}/100 with {confidence}/100 analysis confidence, "
        f"supported by {source_count} source{'s' if source_count != 1 else ''}. "
        f"{trend.why_it_matters or 'Review the evidence before committing resources.'}"
    )


def _is_high_priority(trend_score, opportunity_score) -> bool:
    return (
        trend_score is not None
        and opportunity_score is not None
        and trend_score >= HIGH_PRIORITY_TREND_SCORE
        and opportunity_score >= HIGH_PRIORITY_OPPORTUNITY_SCORE
    )


def _build_context(trend: Trend) -> TrendAnalysisContext:
    sources = [
        SourceSnippet(
            platform=link.platform.name,
            title=link.raw_signal.title,
            summary=link.raw_signal.summary,
            url=link.source_url,
            credibility_weight=link.platform.credibility_weight,
            kuzana_priority_weight=link.platform.kuzana_priority_weight,
            relevance_score=link.relevance_score,
        )
        # Most recent sources first — if there are more than the
        # prompt-building cap (8, see AIProvider._build_user_prompt),
        # the newest coverage of the trend is more useful context than
        # whatever was first.
        for link in trend.source_links.select_related("platform", "raw_signal").order_by(
            "-created_at"
        )
    ]
    return TrendAnalysisContext(
        title=trend.title,
        existing_summary=trend.summary,
        category_name=trend.category.name if trend.category else None,
        sources=sources,
    )


def analyze_trend(trend: Trend, provider_name: str | None = None) -> TrendAnalysis:
    """Runs AI analysis for a trend and persists both the versioned
    TrendAnalysis row and the denormalized latest-scores on Trend
    itself. Safe to call repeatedly — each call adds a new analysis
    row rather than overwriting anything.
    """
    was_high_priority = _is_high_priority(trend.trend_score, trend.opportunity_score)

    provider = get_ai_provider(provider_name)
    context = _build_context(trend)
    result = provider.generate_trend_analysis(context)
    show_opportunity_copy = _should_surface_opportunity_copy(result)
    opportunity_headline = result.opportunity_headline if show_opportunity_copy else ""
    founder_hook = result.founder_hook if show_opportunity_copy else ""
    investor_hook = result.investor_hook if show_opportunity_copy else ""
    creator_hook = result.creator_hook if show_opportunity_copy else ""

    analysis = TrendAnalysis.objects.create(
        trend=trend,
        business_relevance=result.business_relevance,
        founder_relevance=result.founder_relevance,
        entrepreneurship_relevance=result.entrepreneurship_relevance,
        ai_relevance=result.ai_relevance,
        trend_score=result.trend_score,
        opportunity_score=result.opportunity_score,
        confidence_score=result.confidence_score,
        content_creator_score=result.content_creator_score,
        founder_score=result.founder_score,
        investor_score=result.investor_score,
        best_audience=result.best_audience,
        why_it_matters=result.why_it_matters,
        what_is_happening=result.what_is_happening,
        trend_stage=result.trend_stage,
        suggested_content_angle=result.suggested_content_angle,
        kuzana_relevance_score=result.kuzana_relevance_score,
        kuzana_relevance_reason=result.kuzana_relevance_reason,
        kuzana_theme=result.kuzana_theme,
        kuzana_geo_relevance=result.kuzana_geo_relevance,
        kuzana_audience=result.kuzana_audience,
        kuzana_content_format=result.kuzana_content_format,
        kuzana_practical_takeaway=result.kuzana_practical_takeaway,
        opportunity_headline=opportunity_headline,
        founder_hook=founder_hook,
        investor_hook=investor_hook,
        creator_hook=creator_hook,
        model_used=f"{(provider_name or provider.__class__.__name__)}",
    )

    trend.why_spreading = result.why_spreading
    trend.estimated_lifespan = result.estimated_lifespan
    trend.trend_score = result.trend_score
    trend.opportunity_score = result.opportunity_score
    trend.confidence_score = result.confidence_score
    trend.content_creator_score = result.content_creator_score
    trend.founder_score = result.founder_score
    trend.investor_score = result.investor_score
    trend.best_audience = result.best_audience
    trend.why_it_matters = result.why_it_matters
    trend.what_is_happening = result.what_is_happening
    trend.trend_stage = result.trend_stage
    trend.suggested_content_angle = result.suggested_content_angle
    trend.kuzana_relevance_score = result.kuzana_relevance_score
    trend.kuzana_relevance_reason = result.kuzana_relevance_reason
    trend.kuzana_theme = result.kuzana_theme
    trend.kuzana_geo_relevance = result.kuzana_geo_relevance
    trend.kuzana_audience = result.kuzana_audience
    trend.kuzana_content_format = result.kuzana_content_format
    trend.kuzana_practical_takeaway = result.kuzana_practical_takeaway
    trend.opportunity_headline = opportunity_headline
    trend.founder_hook = founder_hook
    trend.investor_hook = investor_hook
    trend.creator_hook = creator_hook
    trend.analyzed_at = timezone.now()
    if not trend.summary and result.summary:
        trend.summary = result.summary

    if trend.category_id is None and result.category_suggestion:
        category, _ = Category.objects.get_or_create(
            name=result.category_suggestion,
        )
        trend.category = category

    trend.action_summary = build_action_summary(trend)

    trend.save(
        update_fields=[
            "why_spreading",
            "estimated_lifespan",
            "trend_score",
            "opportunity_score",
            "confidence_score",
            "content_creator_score",
            "founder_score",
            "investor_score",
            "best_audience",
            "why_it_matters",
            "what_is_happening",
            "trend_stage",
            "suggested_content_angle",
            "kuzana_relevance_score",
            "kuzana_relevance_reason",
            "kuzana_theme",
            "kuzana_geo_relevance",
            "kuzana_audience",
            "kuzana_content_format",
            "kuzana_practical_takeaway",
            "opportunity_headline",
            "founder_hook",
            "investor_hook",
            "creator_hook",
            "action_summary",
            "analyzed_at",
            "summary",
            "category",
            "updated_at",
        ]
    )

    is_high_priority = _is_high_priority(trend.trend_score, trend.opportunity_score)
    if is_high_priority and not was_high_priority:
        notify_all_users(
            NotificationType.NEW_HIGH_VALUE_TREND,
            {
                "trend_id": str(trend.id),
                "trend_slug": trend.slug,
                "title": trend.title,
                "trend_score": trend.trend_score,
                "opportunity_score": trend.opportunity_score,
            },
        )

    return analysis
