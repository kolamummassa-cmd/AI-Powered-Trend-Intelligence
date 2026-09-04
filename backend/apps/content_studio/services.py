from ai_providers import get_ai_provider
from ai_providers.base import ContentBriefContext, ContentPieceContext
from django.db import IntegrityError, transaction
from django.db.models import Max
from apps.content_studio.models import ContentBrief, GeneratedContent
from apps.trends.models import Trend

# Which ContentBrief angle backs each content_type's generation prompt.
# A deliberate, simple mapping rather than letting the caller pick —
# keeps "generate a hook" a one-click action from the trend detail page.
ANGLE_FIELD_FOR_CONTENT_TYPE = {
    "hook": "founder_angle",
    "script_30": "business_angle",
    "post": "marketing_angle",
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
        kuzana_relevance_reason=trend.kuzana_relevance_reason,
        kuzana_theme=trend.kuzana_theme,
        kuzana_geo_relevance=trend.kuzana_geo_relevance,
        kuzana_audience=trend.kuzana_audience,
        kuzana_content_format=trend.kuzana_content_format,
        kuzana_practical_takeaway=trend.kuzana_practical_takeaway,
        opportunity_headline=trend.opportunity_headline,
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
    (Content Perspective) sets the audience lens for every generated
    piece. It is combined with the per-content-type angle so a hook,
    script, post, thumbnail, and reusable template do not all start
    from the same generic instruction.
    """
    angle_field = ANGLE_FIELD_FOR_CONTENT_TYPE.get(content_type, "business_angle")
    format_angle = getattr(brief, angle_field, "") or brief.business_angle
    if brief.content_angle and format_angle:
        angle = f"Audience focus: {brief.content_angle}\n\nFormat focus: {format_angle}"
    else:
        angle = brief.content_angle or format_angle

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

    # Lock the parent brief before allocating a version. The unique constraint
    # remains the final database guard if two workers race across DBs.
    with transaction.atomic():
        locked_brief = ContentBrief.objects.select_for_update().get(id=brief.id)
        latest_version = (
            GeneratedContent.objects.filter(brief=locked_brief, content_type=content_type)
            .aggregate(latest=Max("version"))["latest"]
            or 0
        )
        try:
            return GeneratedContent.objects.create(
                brief=locked_brief,
                created_by=user if user and user.is_authenticated else None,
                content_type=content_type,
                body=result.body,
                version=latest_version + 1,
                model_used=provider_name or provider.__class__.__name__,
            )
        except IntegrityError:
            # Callers can safely retry instead of silently overwriting a version.
            raise
