from django.db import models

from apps.core.models import BaseModel
from apps.trends.models import AudienceType, Trend, TrendStage


class TrendAnalysis(BaseModel):
    """One AI analysis run for a Trend. Deliberately a plain FK (not
    OneToOne) so re-analyzing a trend never destroys the previous
    result — useful both for improving prompts over time without
    losing history, and for defensibility ("why did this score
    change?") when this ends up in front of an investor or a user.

    Trend.trend_score/opportunity_score/confidence_score (and, as of
    the audience-relevance/intelligence fields below, everything else
    here) always reflect the *latest* row here; this table is the full
    history.
    """

    trend = models.ForeignKey(Trend, on_delete=models.CASCADE, related_name="analyses")

    business_relevance = models.TextField()
    founder_relevance = models.TextField()
    entrepreneurship_relevance = models.TextField()
    ai_relevance = models.TextField()

    trend_score = models.PositiveSmallIntegerField()
    opportunity_score = models.PositiveSmallIntegerField()
    confidence_score = models.PositiveSmallIntegerField()

    # Audience relevance (0-100 each) + the best_audience derived from
    # them in code — see Trend's docstring for why best_audience is
    # never trusted directly from the AI's own JSON. Defaults below
    # exist only so this migration doesn't need a one-off backfill
    # value; every real row sets all of these explicitly on create().
    content_creator_score = models.PositiveSmallIntegerField(default=0)
    founder_score = models.PositiveSmallIntegerField(default=0)
    investor_score = models.PositiveSmallIntegerField(default=0)
    best_audience = models.CharField(
        max_length=20, choices=AudienceType.choices, default=AudienceType.FOUNDERS
    )

    why_it_matters = models.TextField(default="")
    what_is_happening = models.TextField(default="")
    trend_stage = models.CharField(
        max_length=20, choices=TrendStage.choices, default=TrendStage.EMERGING
    )
    suggested_content_angle = models.TextField(default="")

    model_used = models.CharField(max_length=100)
    prompt_version = models.CharField(max_length=20, default="v1")

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "trend analyses"
        indexes = [models.Index(fields=["trend", "created_at"])]

    def __str__(self):
        return f"Analysis of {self.trend.title} ({self.created_at:%Y-%m-%d})"
