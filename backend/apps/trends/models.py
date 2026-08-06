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


class Trend(BaseModel):
    """A real-world trend, deduplicated across however many platforms
    are reporting on it. Everything AI-derived (why_spreading, scores,
    confidence) is intentionally nullable here — Phase 2 only proves a
    trend was detected and where from; Phase 3 fills in why it matters.
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

    class Meta:
        ordering = ["-last_seen_at"]
        indexes = [
            models.Index(fields=["status", "last_seen_at"]),
            models.Index(fields=["first_detected_at"]),
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
