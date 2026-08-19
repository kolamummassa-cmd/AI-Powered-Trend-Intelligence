from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SourceSnippet:
    """One platform's take on a trend, fed to the model as context."""

    platform: str
    title: str
    summary: str = ""
    url: str = ""


@dataclass
class TrendAnalysisContext:
    """Everything the model gets to work with. Deliberately just the
    trend's own data plus what its sources reported — no scraping of
    the live page, no images yet.
    """

    title: str
    existing_summary: str = ""
    category_name: str | None = None
    sources: list[SourceSnippet] = field(default_factory=list)


@dataclass
class TrendAnalysisResult:
    business_relevance: str
    founder_relevance: str
    entrepreneurship_relevance: str
    ai_relevance: str
    why_spreading: str
    estimated_lifespan: str
    trend_score: int
    opportunity_score: int
    confidence_score: int
    # Audience relevance (0-100 each), the persona it's derived to fit
    # best, and the rest of the "trend intelligence" block. See
    # apps.trends.models.Trend's docstring for why best_audience is
    # computed here in code rather than trusted from the model's JSON.
    content_creator_score: int = 0
    founder_score: int = 0
    investor_score: int = 0
    best_audience: str = ""
    why_it_matters: str = ""
    what_is_happening: str = ""
    trend_stage: str = ""
    suggested_content_angle: str = ""
    summary: str = ""
    category_suggestion: str | None = None


class AIProviderError(Exception):
    """Raised for anything that isn't the model's fault to fix by
    retrying with the same input — bad config, malformed response,
    unrecoverable API errors. Celery tasks decide whether to retry
    based on this vs. a transient network error.
    """


REQUIRED_ANALYSIS_FIELDS = (
    "business_relevance",
    "founder_relevance",
    "entrepreneurship_relevance",
    "ai_relevance",
    "why_spreading",
    "estimated_lifespan",
    "trend_score",
    "opportunity_score",
    "confidence_score",
    "content_creator_score",
    "founder_score",
    "investor_score",
    "why_it_matters",
    "what_is_happening",
    "trend_stage",
    "suggested_content_angle",
)

# AUDIENCE_SCORE_FIELDS maps each persona to its score key on both the
# parsed result and the Trend/TrendAnalysis models — one place to
# extend if a fourth persona is ever added.
AUDIENCE_SCORE_FIELDS = {
    "content_creators": "content_creator_score",
    "founders": "founder_score",
    "investors": "investor_score",
}

TREND_STAGE_CHOICES = ("emerging", "growing", "peaking", "declining")


def _compute_best_audience(scores: dict) -> str:
    """BEST AUDIENCE is always derived here from the three numeric
    scores — never taken verbatim from the model's own JSON — so it
    can never drift out of sync with the numbers displayed next to it.
    Ties break in a fixed order (founders, then investors, then content
    creators) purely for determinism; a genuine 3-way tie is rare given
    0-100 integer scores from a real analysis.
    """
    tie_break_order = ("founders", "investors", "content_creators")
    return max(tie_break_order, key=lambda audience: scores[AUDIENCE_SCORE_FIELDS[audience]])


def parse_analysis_response(data: dict) -> TrendAnalysisResult:
    """Shared validation for both providers so 'the model returned
    garbage' fails the same way regardless of which model it was.
    """
    missing = [f for f in REQUIRED_ANALYSIS_FIELDS if f not in data]
    if missing:
        raise AIProviderError(f"AI response missing required field(s): {missing}")

    scores = {}
    for key in (
        "trend_score",
        "opportunity_score",
        "confidence_score",
        "content_creator_score",
        "founder_score",
        "investor_score",
    ):
        try:
            value = int(data[key])
        except (TypeError, ValueError):
            raise AIProviderError(f"'{key}' must be an integer, got {data[key]!r}")
        if not 0 <= value <= 100:
            raise AIProviderError(f"'{key}' must be between 0 and 100, got {value}")
        scores[key] = value

    trend_stage = str(data["trend_stage"]).strip().lower()
    if trend_stage not in TREND_STAGE_CHOICES:
        raise AIProviderError(
            f"'trend_stage' must be one of {TREND_STAGE_CHOICES}, got {trend_stage!r}"
        )

    best_audience = _compute_best_audience(scores)

    return TrendAnalysisResult(
        business_relevance=str(data["business_relevance"]).strip(),
        founder_relevance=str(data["founder_relevance"]).strip(),
        entrepreneurship_relevance=str(data["entrepreneurship_relevance"]).strip(),
        ai_relevance=str(data["ai_relevance"]).strip(),
        why_spreading=str(data["why_spreading"]).strip(),
        estimated_lifespan=str(data["estimated_lifespan"]).strip(),
        best_audience=best_audience,
        why_it_matters=str(data["why_it_matters"]).strip(),
        what_is_happening=str(data["what_is_happening"]).strip(),
        trend_stage=trend_stage,
        suggested_content_angle=str(data["suggested_content_angle"]).strip(),
        summary=str(data.get("summary", "")).strip(),
        category_suggestion=(
            str(data["category_suggestion"]).strip() if data.get("category_suggestion") else None
        ),
        **scores,
    )


ANALYSIS_SYSTEM_PROMPT = """You are a trend analyst for a platform that helps startup founders, \
entrepreneurs, investors, and content creators act on trends while they're still relevant. \
Given a trend title and snippets from where it's being discussed, analyze it and respond with \
ONLY a JSON object (no markdown, no commentary) with exactly these keys:

- business_relevance: string, 1-2 sentences on why this matters for businesses generally
- founder_relevance: string, 1-2 sentences on why this matters specifically for startup founders
- entrepreneurship_relevance: string, 1-2 sentences on the opportunity for entrepreneurs
- ai_relevance: string, 1-2 sentences on any AI angle (or "Not directly AI-related" if none)
- why_spreading: string, 1-2 sentences on why this is gaining attention right now
- estimated_lifespan: short string like "2-3 weeks" or "several months"
- trend_score: integer 0-100, how significant/widespread this trend currently is
- opportunity_score: integer 0-100, how actionable this is for a creator/founder right now
- confidence_score: integer 0-100, your confidence in this analysis given the available context
- content_creator_score: integer 0-100, how relevant/actionable this trend is specifically for \
short-form content creators looking to make something about it
- founder_score: integer 0-100, how relevant this trend is specifically for startup founders \
building a product or company
- investor_score: integer 0-100, how relevant this trend is specifically for investors deciding \
where to put attention or capital
- why_it_matters: string, 2-3 sentences on why this trend matters right now, written so it makes \
sense regardless of which audience is reading it
- what_is_happening: string, 1-2 sentences plainly explaining the actual event or development
- trend_stage: one of exactly "emerging", "growing", "peaking", "declining" — this trend's current \
lifecycle stage
- suggested_content_angle: string, one concrete, specific content angle a creator could use to \
cover this trend (not generic advice — reference the actual trend)
- summary: string, 2-3 sentence neutral summary of the trend itself
- category_suggestion: short string category name (e.g. "Fintech", "AI Tools", "Politics"), or null

Respond with raw JSON only."""


PERSPECTIVE_LABELS = {
    "content_creators": "a content creator making short-form content for an audience",
    "founders": "a startup founder building a product or company",
    "investors": "an investor evaluating where to put attention or capital",
}


@dataclass
class ContentBriefContext:
    """What Phase 5 content generation has to work with — the trend
    plus whatever Phase 3 analysis already figured out, so the brief
    doesn't have to re-derive relevance from scratch.

    The fields from `perspective` onward are the Content Perspective
    layer: everything the trend-intelligence pipeline already knows
    (scores, best audience, stage, lifespan, why it matters), fed in so
    `content_angle` can be genuinely grounded in the trend rather than
    generic advice, and skewed toward whichever persona the user chose
    — which may or may not be the trend's best_audience.
    """

    trend_title: str
    trend_summary: str = ""
    why_spreading: str = ""
    business_relevance: str = ""
    founder_relevance: str = ""
    entrepreneurship_relevance: str = ""
    ai_relevance: str = ""
    perspective: str = ""
    trend_score: int | None = None
    opportunity_score: int | None = None
    best_audience: str = ""
    why_it_matters: str = ""
    trend_stage: str = ""
    estimated_lifespan: str = ""


@dataclass
class ContentBriefResult:
    business_angle: str
    founder_angle: str
    educational_angle: str
    marketing_angle: str
    talking_points: list[str] = field(default_factory=list)
    # The Content Perspective angle — always present, but only actually
    # written from a specific persona's point of view when a perspective
    # was given in the context; otherwise it's a well-rounded general
    # angle, same spirit as the four fields above.
    content_angle: str = ""


CONTENT_BRIEF_REQUIRED_FIELDS = (
    "business_angle",
    "founder_angle",
    "educational_angle",
    "marketing_angle",
    "talking_points",
    "content_angle",
)


def parse_content_brief_response(data: dict) -> ContentBriefResult:
    missing = [f for f in CONTENT_BRIEF_REQUIRED_FIELDS if f not in data]
    if missing:
        raise AIProviderError(f"AI response missing required field(s): {missing}")

    talking_points = data["talking_points"]
    if not isinstance(talking_points, list):
        raise AIProviderError("'talking_points' must be a list of strings")

    return ContentBriefResult(
        business_angle=str(data["business_angle"]).strip(),
        founder_angle=str(data["founder_angle"]).strip(),
        educational_angle=str(data["educational_angle"]).strip(),
        marketing_angle=str(data["marketing_angle"]).strip(),
        talking_points=[str(point).strip() for point in talking_points],
        content_angle=str(data["content_angle"]).strip(),
    )


CONTENT_BRIEF_SYSTEM_PROMPT = """You are a content strategist for a platform that turns trends \
into publishable short-form content for founders, entrepreneurs, investors, and creators. Given \
a trend and why it matters, respond with ONLY a JSON object (no markdown, no commentary) with \
exactly these keys:

- business_angle: string, 2-3 sentences on how to frame this trend for a general business audience
- founder_angle: string, 2-3 sentences on how a startup founder specifically could talk about this
- educational_angle: string, 2-3 sentences on explaining this trend to an unfamiliar audience
- marketing_angle: string, 2-3 sentences on how a brand/marketer could use this trend
- talking_points: array of 4-6 short strings, concrete specific points a creator could use verbatim
- content_angle: string, 2-3 sentences proposing ONE specific, concrete content angle for this \
trend. If a "Content Perspective" is given in the prompt, write this specifically from that \
persona's point of view — the tone and focus should clearly differ between a content creator, a \
founder, and an investor angle on the same trend. If no perspective is given, write a \
well-rounded general angle.

Respond with raw JSON only."""


@dataclass
class ContentPieceContext:
    """Everything needed to generate one piece of content. `angle` is
    whichever ContentBrief field the caller decided is most relevant
    for this content_type (e.g. founder_angle for a founder-focused
    hook) — chosen by the service layer, not the AI provider.

    `perspective`, when set, is the Content Perspective the user chose
    for the parent brief — it's the strongest single influence on tone
    for every content type (hook, script, CTA, hashtags, remix), per
    product spec, which is why it's threaded all the way down here
    rather than just shaping the brief's angle.
    """

    trend_title: str
    content_type: str
    angle: str
    talking_points: list[str] = field(default_factory=list)
    tone: str = "confident, concise, platform-native"
    perspective: str = ""


@dataclass
class ContentPieceResult:
    body: str


CONTENT_TYPE_INSTRUCTIONS = {
    "hook": (
        "Write 3 short, scroll-stopping hook lines (one sentence each) for a short-form "
        "video about this trend. Return them as separate lines, no numbering."
    ),
    "script_30": (
        "Write a ~30 second short-form video script (roughly 75-90 words) with a hook, one "
        "core point, and a closing line. Plain text, no scene directions."
    ),
    "script_60": (
        "Write a ~60 second short-form video script (roughly 150-170 words) with a hook, "
        "2-3 key points, and a closing line. Plain text, no scene directions."
    ),
    "cta": "Write 3 short call-to-action lines suitable for the end of a short-form video or post.",
    "hashtags": (
        "Write 8-12 relevant hashtags for this content, space-separated on one line, no "
        "explanations."
    ),
    "thumbnail_suggestion": (
        "Describe a compelling thumbnail concept in 2-3 sentences: composition, any text "
        "overlay, and the expression/emotion to convey."
    ),
    "remix_template": (
        "Describe a reusable content format/template other creators could remix for this "
        "trend, in 3-4 sentences."
    ),
}


def content_piece_system_prompt(content_type: str) -> str:
    instruction = CONTENT_TYPE_INSTRUCTIONS.get(content_type)
    if not instruction:
        raise AIProviderError(f"Unknown content_type: {content_type!r}")
    return (
        "You are a short-form content writer for founders, entrepreneurs, and creators "
        "acting on trends while they're still relevant. "
        f"{instruction} Respond with plain text only — no markdown, no commentary, no JSON."
    )


@dataclass
class ChatRefineContext:
    """One turn of the Phase 6 AI Chat: the content being refined, its
    history so far, and the user's latest instruction.
    """

    content_body: str
    content_type: str
    instruction: str
    history: list[tuple[str, str]] = field(default_factory=list)  # (role, message)


@dataclass
class ChatRefineResult:
    reply: str


CHAT_REFINE_SYSTEM_PROMPT = """You are refining a piece of short-form content on a founder's \
request, in an ongoing conversation. Make the change they ask for while keeping the content's \
original intent and format. Respond with ONLY the revised content body — no markdown fencing, \
no commentary, no explanation of what changed."""


class AIProvider(ABC):
    """Everything AI-related in the platform goes through a subclass
    of this — trend analysis, content generation, and chat refinement.
    Swapping OpenAI for Claude (or vice versa) is a settings change,
    never a call-site change.
    """

    @abstractmethod
    def generate_trend_analysis(self, context: TrendAnalysisContext) -> TrendAnalysisResult:
        raise NotImplementedError

    @abstractmethod
    def generate_content_brief(self, context: ContentBriefContext) -> ContentBriefResult:
        raise NotImplementedError

    @abstractmethod
    def generate_content_piece(self, context: ContentPieceContext) -> ContentPieceResult:
        raise NotImplementedError

    @abstractmethod
    def chat_refine(self, context: ChatRefineContext) -> ChatRefineResult:
        raise NotImplementedError

    @staticmethod
    def _build_user_prompt(context: TrendAnalysisContext) -> str:
        lines = [f"Trend title: {context.title}"]
        if context.category_name:
            lines.append(f"Existing category: {context.category_name}")
        if context.existing_summary:
            lines.append(f"Existing summary: {context.existing_summary}")
        if context.sources:
            lines.append("\nSource snippets:")
            for src in context.sources[:8]:
                lines.append(f"- [{src.platform}] {src.title}: {src.summary[:300]}")
        return "\n".join(lines)

    @staticmethod
    def _build_content_brief_prompt(context: ContentBriefContext) -> str:
        lines = [f"Trend: {context.trend_title}"]
        if context.trend_summary:
            lines.append(f"Summary: {context.trend_summary}")
        if context.why_spreading:
            lines.append(f"Why it's spreading: {context.why_spreading}")
        if context.business_relevance:
            lines.append(f"Business relevance: {context.business_relevance}")
        if context.founder_relevance:
            lines.append(f"Founder relevance: {context.founder_relevance}")
        if context.entrepreneurship_relevance:
            lines.append(f"Entrepreneurship relevance: {context.entrepreneurship_relevance}")
        if context.ai_relevance:
            lines.append(f"AI relevance: {context.ai_relevance}")
        if context.why_it_matters:
            lines.append(f"Why it matters: {context.why_it_matters}")
        if context.trend_stage:
            lines.append(f"Trend stage: {context.trend_stage}")
        if context.estimated_lifespan:
            lines.append(f"Estimated lifespan: {context.estimated_lifespan}")
        if context.trend_score is not None:
            lines.append(f"Trend score: {context.trend_score}/100")
        if context.opportunity_score is not None:
            lines.append(f"Opportunity score: {context.opportunity_score}/100")
        if context.best_audience:
            lines.append(
                f"Best audience (intelligence signal only, not a restriction): "
                f"{context.best_audience}"
            )
        if context.perspective:
            label = PERSPECTIVE_LABELS.get(context.perspective, context.perspective)
            lines.append(
                f"\nContent Perspective: {context.perspective} — write the content_angle as if "
                f"speaking to {label}. This is the user's chosen point of view for creating "
                f"content and should be honored even if it differs from the best audience above."
            )
        return "\n".join(lines)

    @staticmethod
    def _build_content_piece_prompt(context: ContentPieceContext) -> str:
        lines = [f"Trend: {context.trend_title}", f"Angle to use: {context.angle}"]
        if context.talking_points:
            lines.append("Talking points:")
            lines.extend(f"- {point}" for point in context.talking_points)
        if context.perspective:
            label = PERSPECTIVE_LABELS.get(context.perspective, context.perspective)
            lines.append(
                f"\nContent Perspective: {context.perspective} — this is the single strongest "
                f"influence on tone and framing. Write as if speaking to {label}, even if that "
                f"differs from who the trend is naturally most relevant to."
            )
        lines.append(f"Tone: {context.tone}")
        return "\n".join(lines)

    @staticmethod
    def _build_chat_history_messages(context: ChatRefineContext) -> list[dict]:
        messages = [
            {
                "role": "user",
                "content": (
                    f"Here is the current content ({context.content_type}):\n\n"
                    f"{context.content_body}"
                ),
            }
        ]
        for role, message in context.history:
            messages.append({"role": role, "content": message})
        messages.append({"role": "user", "content": context.instruction})
        return messages
