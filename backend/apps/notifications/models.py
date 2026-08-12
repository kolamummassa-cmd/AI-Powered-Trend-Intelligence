from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class NotificationType(models.TextChoices):
    NEW_HIGH_VALUE_TREND = "new_high_value_trend", "New high-value trend"
    EXPIRING_TREND = "expiring_trend", "Expiring trend"
    GENERATION_COMPLETE = "generation_complete", "Generation complete"


class Notification(BaseModel):
    """In-app first (per the roadmap) — email delivery can hang off
    the same trigger points later without touching this model.
    `payload` carries whatever the frontend needs to render and link
    to the right place (trend slug, content id, etc.) without another
    query per notification.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    type = models.CharField(max_length=30, choices=NotificationType.choices)
    payload = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "read_at"])]

    def __str__(self):
        return f"{self.get_type_display()} for {self.user_id}"
