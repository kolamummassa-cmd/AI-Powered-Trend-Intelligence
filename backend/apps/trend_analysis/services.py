from ai_providers import get_ai_provider
from ai_providers.base import SourceSnippet, TrendAnalysisContext
from apps.trend_analysis.models import TrendAnalysis
from apps.trend_analysis.evidence import EvidenceResult, verify_trend_evidence
from apps.trends.models import Trend


OPPORTUNITY_HEADLINE_MIN_CONFIDENCE_SCORE = 60


def _should_surface_opportunity_copy(result) -> bool:
    """Only turn a source headline into editorial copy when evidence is sufficient."""
    return result.confidence_score >= OPPORTUNITY_HEADLINE_MIN_CONFIDENCE_SCORE and bool(
        result.opportunity_headline
    )


def build_action_summary(
    trend: Trend,
    *,
    opportunity_score: int,
    evidence_score: int,
    trend_stage: str,
    why_it_matters: str,
) -> str:
    """A deterministic, concise decision aid—never an untraceable extra AI claim."""
    source_count = trend.source_links.count()
    urgency = "Act now" if trend_stage in {"emerging", "growing"} else "Monitor closely"
    return (
        f"{urgency}: opportunity is {opportunity_score}/100 with "
        f"{evidence_score}/100 evidence strength, "
        f"supported by {source_count} source{'s' if source_count != 1 else ''}. "
        f"{why_it_matters or 'Review the evidence before committing resources.'}"
    )


def _build_context(trend: Trend, evidence: EvidenceResult) -> TrendAnalysisContext:
    feed_sources = [
        SourceSnippet(
            platform=link.platform.name,
            title=link.raw_signal.title,
            summary=link.raw_signal.summary,
            url=link.source_url,
            published_at=link.raw_signal.published_at,
            credibility_weight=link.platform.credibility_weight,
            kuzana_priority_weight=link.platform.kuzana_priority_weight,
            relevance_score=link.relevance_score,
        )
        # Most recent sources first. Five leave room for up to three freshly
        # verified web sources in the model context.
        for link in trend.source_links.select_related("platform", "raw_signal").order_by(
            "-created_at"
        )
    ][:5]
    return TrendAnalysisContext(
        title=trend.title,
        existing_summary=trend.source_excerpt or trend.summary,
        category_name=trend.category.name if trend.category else None,
        sources=feed_sources + evidence.external_sources,
    )


def analyze_trend(trend: Trend, user=None, provider_name: str | None = None) -> TrendAnalysis:
    """Run an analysis without mutating the shared RSS trend.

    ``user`` owns the result. Calls without a user are supported for internal
    jobs, but their result is intentionally not shown to customer accounts.
    """

    provider = get_ai_provider(provider_name)
    evidence = verify_trend_evidence(trend)
    context = _build_context(trend, evidence)
    result = provider.generate_trend_analysis(context)
    show_opportunity_copy = _should_surface_opportunity_copy(result)
    opportunity_headline = result.opportunity_headline if show_opportunity_copy else ""
    founder_hook = result.founder_hook if show_opportunity_copy else ""
    investor_hook = result.investor_hook if show_opportunity_copy else ""
    creator_hook = result.creator_hook if show_opportunity_copy else ""

    analysis = TrendAnalysis.objects.create(
        trend=trend,
        created_by=user if user and user.is_authenticated else None,
        summary=result.summary or result.what_is_happening,
        why_spreading=result.why_spreading,
        estimated_lifespan=result.estimated_lifespan,
        action_summary=build_action_summary(
            trend,
            opportunity_score=result.opportunity_score,
            evidence_score=evidence.score,
            trend_stage=result.trend_stage,
            why_it_matters=result.why_it_matters,
        ),
        business_relevance=result.business_relevance,
        founder_relevance=result.founder_relevance,
        entrepreneurship_relevance=result.entrepreneurship_relevance,
        ai_relevance=result.ai_relevance,
        trend_score=result.trend_score,
        opportunity_score=result.opportunity_score,
        evidence_score=evidence.score,
        evidence_source_count=evidence.feed_source_count,
        verified_source_count=evidence.verified_source_count,
        evidence_summary=evidence.summary,
        confidence_score=result.confidence_score,
        content_creator_score=result.content_creator_score,
        founder_score=result.founder_score,
        investor_score=result.investor_score,
        best_audience=result.best_audience,
        why_it_matters=result.why_it_matters,
        what_is_happening=result.what_is_happening,
        trend_stage=result.trend_stage,
        suggested_content_angle=result.suggested_content_angle,
        opportunity_headline=opportunity_headline,
        founder_hook=founder_hook,
        investor_hook=investor_hook,
        creator_hook=creator_hook,
        model_used=f"{(provider_name or provider.__class__.__name__)}",
        prompt_version="v2",
    )
    return analysis
