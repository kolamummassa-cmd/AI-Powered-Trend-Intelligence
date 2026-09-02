from django.db import models

from apps.core.models import BaseModel


class Platform(BaseModel):
    """One row per monitored source (Google Trends, a specific
    subreddit, an RSS feed...). `adapter_key` maps to whichever
    TrendSourceAdapter subclass knows how to poll it; `config` carries
    whatever that adapter needs (feed URL, subreddit name, etc.) so
    adding another RSS feed is a new row, not new code.
    """

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    adapter_key = models.CharField(
        max_length=50, help_text="Must match a slug registered via @register_adapter."
    )
    config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    poll_interval_minutes = models.PositiveIntegerField(default=60)
    credibility_weight = models.PositiveSmallIntegerField(
        default=50,
        help_text="Editorial credibility score from 0-100, used as one input to AI analysis.",
    )
    kuzana_priority_weight = models.PositiveSmallIntegerField(
        default=50,
        help_text=(
            "Kuzana editorial priority from 0-100. Higher values make a source's "
            "evidence more influential when deciding relevance for Kenyan founders."
        ),
    )
    last_polled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def is_due(self, now) -> bool:
        if not self.is_active:
            return False
        if self.last_polled_at is None:
            return True
        elapsed = (now - self.last_polled_at).total_seconds() / 60
        return elapsed >= self.poll_interval_minutes


class RawTrendSignal(BaseModel):
    """The unprocessed thing an adapter fetched, before dedup/scoring
    decides whether it becomes a new Trend or gets attached to an
    existing one. Kept indefinitely (soft-delete only) as an audit
    trail of exactly what each source reported and when.
    """

    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name="raw_signals")
    external_id = models.CharField(max_length=255)
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=1000, blank=True)
    summary = models.TextField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["platform", "external_id"], name="unique_signal_per_platform"
            )
        ]
        indexes = [
            models.Index(fields=["platform", "created_at"]),
            models.Index(fields=["processed_at"]),
        ]

    def __str__(self):
        return f"{self.platform.slug}: {self.title[:50]}"
