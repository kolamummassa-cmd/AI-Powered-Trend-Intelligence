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

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.trend.title} <- {self.platform.slug}"
