from django.conf import settings
from django.db import models

from apps.core.models import BaseModel
from apps.trends.models import AudienceType, Trend


class ContentBrief(BaseModel):
    """The strategic groundwork for one trend, generated once and then
    reused to produce as many content pieces (hooks, scripts, etc.) as
    the user wants — regenerating the brief itself is a deliberate,
    separate action so a user doesn't lose their angle every time they
    ask for one more hook.
    """

    trend = models.ForeignKey(Trend, on_delete=models.CASCADE, related_name="content_briefs")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="content_briefs",
    )

    business_angle = models.TextField(blank=True)
    founder_angle = models.TextField(blank=True)
    educational_angle = models.TextField(blank=True)
    marketing_angle = models.TextField(blank=True)
    talking_points = models.JSONField(default=list, blank=True)

    # CONTENT PERSPECTIVE: the persona the *user* chose to create
    # content from — independent of Trend.best_audience (an intelligence
    # signal about the trend itself, not a restriction on who may act on
    # it). content_angle is the angle generated specifically for that
    # perspective; the four *_angle fields above are the original,
    # unrelated angle breakdown and are left untouched for backward
    # compatibility.
    perspective = models.CharField(
        max_length=20, choices=AudienceType.choices, blank=True, default=""
    )
    content_angle = models.TextField(blank=True, default="")

    model_used = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["trend", "created_at"])]

    def __str__(self):
        return f"Brief for {self.trend.title}"


class ContentType(models.TextChoices):
    HOOK = "hook", "Hook"
    SCRIPT_30 = "script_30", "30s script"
    SCRIPT_60 = "script_60", "60s script"
    CTA = "cta", "Call to action"
    HASHTAGS = "hashtags", "Hashtags"
    THUMBNAIL_SUGGESTION = "thumbnail_suggestion", "Thumbnail suggestion"
    REMIX_TEMPLATE = "remix_template", "Remix template"


class GeneratedContent(BaseModel):
    """One piece of publishable content derived from a ContentBrief.
    Versioned (rather than overwritten) so "regenerate this hook"
    keeps prior attempts around — useful for comparing options before
    picking one to save.
    """

    brief = models.ForeignKey(
        ContentBrief, on_delete=models.CASCADE, related_name="generated_content"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_content",
    )

    content_type = models.CharField(max_length=30, choices=ContentType.choices)
    body = models.TextField()
    version = models.PositiveSmallIntegerField(default=1)
    is_saved = models.BooleanField(default=False)
    model_used = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_by", "is_saved"]),
            models.Index(fields=["brief", "content_type"]),
        ]

    def __str__(self):
        return f"{self.get_content_type_display()} v{self.version} for {self.brief.trend.title}"
