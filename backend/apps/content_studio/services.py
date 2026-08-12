from ai_providers import get_ai_provider
from ai_providers.base import ContentBriefContext, ContentPieceContext
from apps.content_studio.models import ContentBrief, GeneratedContent
from apps.trends.models import Trend

# Which ContentBrief angle backs each content_type's generation prompt.
# A deliberate, simple mapping rather than letting the caller pick —
# keeps "generate a hook" a one-click action from the trend detail page.
ANGLE_FIELD_FOR_CONTENT_TYPE = {
    "hook": "founder_angle",
    "script_30": "business_angle",
    "script_60": "business_angle",
    "cta": "marketing_angle",
    "hashtags": "marketing_angle",
    "thumbnail_suggestion": "educational_angle",
    "remix_template": "educational_angle",
}


def _build_brief_context(trend: Trend, perspective: str = "") -> ContentBriefContext:
    latest_analysis = next(iter(trend.analyses.all()), None)
    return ContentBriefContext(
        trend_title=trend.title,
        trend_summary=trend.summary,
        why_spreading=trend.why_spreading,
        business_relevance=latest_analysis.business_relevance if latest_analysis else "",
        founder_relevance=latest_analysis.founder_relevance if latest_analysis else "",
        entrepreneurship_relevance=(
            latest_analysis.entrepreneurship_relevance if latest_analysis else ""
        ),
        ai_relevance=latest_analysis.ai_relevance if latest_analysis else "",
        perspective=perspective,
        trend_score=trend.trend_score,
        opportunity_score=trend.opportunity_score,
        best_audience=trend.best_audience,
        why_it_matters=trend.why_it_matters,
        trend_stage=trend.trend_stage,
        estimated_lifespan=trend.estimated_lifespan,
    )


def generate_brief(
    trend: Trend,
    user=None,
    provider_name: str | None = None,
    perspective: str = "",
) -> ContentBrief:
    """Generates a fresh ContentBrief for a trend. Callable more than
    once — each call is a new row (see ContentBrief's docstring), so a
    user can regenerate the strategic angle without losing whichever
    content pieces they already generated and saved from a prior brief.

    `perspective` is the user's chosen Content Perspective — distinct
    from Trend.best_audience (an intelligence signal, not a
    restriction). Falls back to the trend's best_audience only when the
    caller doesn't specify one, so the API layer's default pre-selects
    the most relevant persona while always letting a user override it.
    """
    perspective = perspective or trend.best_audience or ""

    provider = get_ai_provider(provider_name)
    context = _build_brief_context(trend, perspective=perspective)
    result = provider.generate_content_brief(context)

    return ContentBrief.objects.create(
        trend=trend,
        created_by=user if user and user.is_authenticated else None,
        business_angle=result.business_angle,
        founder_angle=result.founder_angle,
        educational_angle=result.educational_angle,
        marketing_angle=result.marketing_angle,
        talking_points=result.talking_points,
        perspective=perspective,
        content_angle=result.content_angle,
        model_used=provider_name or provider.__class__.__name__,
    )


def generate_content(
    brief: ContentBrief,
    content_type: str,
    user=None,
    provider_name: str | None = None,
) -> GeneratedContent:
    """Generates one piece of content from a brief. Each call adds a
    new version rather than overwriting a prior attempt at the same
    content_type, so "regenerate this hook" lets a user compare
    options before saving one.

    Angle selection: the brief's perspective-driven `content_angle`
    (Content Perspective) takes priority when present, since the
    product spec calls it the strongest influence on every generated
    piece's tone. The original per-content-type angle mapping is kept
    as the fallback for briefs generated before this existed, or if a
    brief's content_angle is somehow blank.
    """
    if brief.content_angle:
        angle = brief.content_angle
    else:
        angle_field = ANGLE_FIELD_FOR_CONTENT_TYPE.get(content_type, "business_angle")
        angle = getattr(brief, angle_field, "") or brief.business_angle

    provider = get_ai_provider(provider_name)
    result = provider.generate_content_piece(
        ContentPieceContext(
            trend_title=brief.trend.title,
            content_type=content_type,
            angle=angle,
            talking_points=brief.talking_points,
            perspective=brief.perspective,
        )
    )

    previous_count = GeneratedContent.objects.filter(brief=brief, content_type=content_type).count()

    return GeneratedContent.objects.create(
        brief=brief,
        created_by=user if user and user.is_authenticated else None,
        content_type=content_type,
        body=result.body,
        version=previous_count + 1,
        model_used=provider_name or provider.__class__.__name__,
    )
