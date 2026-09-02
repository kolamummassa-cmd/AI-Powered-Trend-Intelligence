import uuid

from django.db import models
from django.utils.text import slugify

from apps.core.models import BaseModel
from apps.trend_sources.models import Platform, RawTrendSignal


class Category(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:100]
        super().save(*args, **kwargs)


class TrendStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    EXPIRING = "expiring", "Expiring"
    EXPIRED = "expired", "Expired"


class AudienceType(models.TextChoices):
    """The three personas the platform serves. Used both for
    Trend.best_audience (an intelligence signal — "who does this trend
    naturally fit best") and ContentBrief.perspective (a user choice —
    "who am I creating content for"). These are deliberately the same
    enum but conceptually distinct; see ContentBrief.perspective's
    docstring for why they must never be confused.
    """

    CONTENT_CREATORS = "content_creators", "Content Creators"
    FOUNDERS = "founders", "Founders"
    INVESTORS = "investors", "Investors"


class TrendStage(models.TextChoices):
    EMERGING = "emerging", "Emerging"
    GROWING = "growing", "Growing"
    PEAKING = "peaking", "Peaking"
    DECLINING = "declining", "Declining"


class KuzanaTheme(models.TextChoices):
    STARTUPS = "startups", "Startups"
    FUNDING = "funding", "Funding"
    FINTECH = "fintech", "Fintech & money"
    SALES_MARKETING = "sales_marketing", "Sales & marketing"
    SIDE_HUSTLES = "side_hustles", "Side hustles"
    CAREERS = "careers", "Careers"
    TECHNOLOGY = "technology", "Technology"
    FOUNDER_STORY = "founder_story", "Founder story"
    CREATOR_ECONOMY = "creator_economy", "Creator economy"
    BUSINESS_POLICY = "business_policy", "Business policy"
    OTHER = "other", "Other"


class KuzanaGeoRelevance(models.TextChoices):
    KENYA = "kenya", "Kenya"
    EAST_AFRICA = "east_africa", "East Africa"
    AFRICA = "africa", "Africa"
    GLOBAL_LESSON = "global_lesson", "Global lesson"
    NOT_RELEVANT = "not_relevant", "Not relevant"


class Trend(BaseModel):
    """A real-world trend, deduplicated across however many platforms
    are reporting on it. why_spreading/estimated_lifespan/scores are
    nullable/blank until the AI analysis pipeline (Phase 3) fills them
    in — a trend is real and listable the moment it's detected, before
    anyone has analyzed why it matters.

    Scores are denormalized here (rather than only living on
    TrendAnalysis) because the dashboard/feed need to sort and filter
    by them cheaply and often; TrendAnalysis is the versioned history
    of *how* those numbers were arrived at, and re-analysis never
    destroys it. The audience-relevance/intelligence fields added
    below follow that exact same denormalization pattern.
    """

    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=320, unique=True)
    dedup_key = models.CharField(
        max_length=300,
        db_index=True,
        help_text="Normalized title used to match new signals to an existing trend.",
    )
    active_dedup_key = models.CharField(max_length=300, null=True, blank=True, unique=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="trends"
    )
    summary = models.TextField(blank=True)
    why_spreading = models.TextField(blank=True)
    estimated_lifespan = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20, choices=TrendStatus.choices, default=TrendStatus.ACTIVE
    )
    first_detected_at = models.DateTimeField(db_index=True)
    last_seen_at = models.DateTimeField(db_index=True)
    # Set at the lifecycle transition, rather than inferred from a feed
    # timestamp, so retention is predictable even when the hourly task is
    # delayed or a trend was imported late.
    expired_at = models.DateTimeField(null=True, blank=True, db_index=True)
    # Administrators can keep a record beyond normal retention where a legal,
    # contractual, or audit obligation applies.
    retention_required = models.BooleanField(default=False)

    trend_score = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)
    opportunity_score = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)
    confidence_score = models.PositiveSmallIntegerField(null=True, blank=True)
    analyzed_at = models.DateTimeField(null=True, blank=True)

    # --- Audience relevance & trend intelligence -----------------------
    # AUDIENCE RELEVANCE: how relevant this trend is to each persona,
    # 0-100, set by AI analysis. BEST AUDIENCE: derived in code (never
    # trusted blindly from the model's own JSON) from whichever of the
    # three scores is highest — see ai_providers.base.parse_analysis_response.
    # These two concepts, plus ContentBrief.perspective (a user choice),
    # must stay distinct throughout the app.
    content_creator_score = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)
    founder_score = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)
    investor_score = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)
    best_audience = models.CharField(
        max_length=20, choices=AudienceType.choices, blank=True, default="", db_index=True
    )

    why_it_matters = models.TextField(blank=True, default="")
    what_is_happening = models.TextField(blank=True, default="")
    trend_stage = models.CharField(
        max_length=20, choices=TrendStage.choices, blank=True, default=""
    )
    suggested_content_angle = models.TextField(blank=True, default="")
    action_summary = models.TextField(blank=True, default="")

    # Structured Kuzana editorial classifications keep the feed useful to
    # Kenyan founders, entrepreneurs, and business-minded creators.
    kuzana_relevance_score = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)
    kuzana_relevance_reason = models.TextField(blank=True, default="")
    kuzana_theme = models.CharField(max_length=30, choices=KuzanaTheme.choices, blank=True, default="")
    kuzana_geo_relevance = models.CharField(
        max_length=20, choices=KuzanaGeoRelevance.choices, blank=True, default=""
    )
    kuzana_audience = models.CharField(max_length=100, blank=True, default="")
    kuzana_content_format = models.CharField(max_length=50, blank=True, default="")
    kuzana_practical_takeaway = models.TextField(blank=True, default="")

    # Editorial copy derived from an analysis. The original `title` always
    # remains the source headline; these fields only provide a clearer,
    # Kuzana-facing reason to open the trend when the evidence is strong.
    opportunity_headline = models.CharField(max_length=180, blank=True, default="")
    founder_hook = models.CharField(max_length=240, blank=True, default="")
    investor_hook = models.CharField(max_length=240, blank=True, default="")
    creator_hook = models.CharField(max_length=240, blank=True, default="")

    class Meta:
        ordering = ["-last_seen_at"]
        indexes = [
            models.Index(fields=["status", "last_seen_at"]),
            models.Index(fields=["first_detected_at"]),
            models.Index(fields=["trend_score"]),
            models.Index(fields=["opportunity_score"]),
            models.Index(fields=["best_audience"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:80] or "trend"
            self.slug = f"{base}-{uuid.uuid4().hex[:8]}"
        self.active_dedup_key = None if self.status == TrendStatus.EXPIRED else self.dedup_key
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            kwargs["update_fields"] = set(update_fields) | {"active_dedup_key"}
        super().save(*args, **kwargs)


class TrendSourceLink(BaseModel):
    """Connects a Trend to one specific RawTrendSignal that fed it —
    a trend spotted on three platforms has three of these. Kept
    OneToOne on raw_signal because each raw signal is processed by the
    ingestion pipeline exactly once (see apps.trends.tasks.ingest_signal).
    """

    trend = models.ForeignKey(Trend, on_delete=models.CASCADE, related_name="source_links")
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name="trend_links")
    raw_signal = models.OneToOneField(
        RawTrendSignal, on_delete=models.CASCADE, related_name="trend_link"
    )
    source_url = models.URLField(max_length=1000, blank=True)
    relevance_score = models.PositiveSmallIntegerField(default=50)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["trend", "-created_at"])]

    def __str__(self):
        return f"{self.trend.title} <- {self.platform.slug}"
