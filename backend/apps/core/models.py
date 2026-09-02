import uuid

from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)

    def delete(self):
        """Bulk soft delete instead of removing rows."""
        return super().update(deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()


class SoftDeleteManager(models.Manager):
    """Default manager: only ever returns non-deleted rows.

    Use `all_objects` on a model to reach soft-deleted rows when that is
    genuinely required (e.g. admin tooling, audits).
    """

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()


class AllObjectsManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class BaseModel(models.Model):
    """Base for every domain model in the platform.

    Provides a UUID primary key (safe to expose in APIs, doesn't leak
    row counts/insert order), audit timestamps, and soft delete. Every
    feature-app model should inherit from this rather than models.Model
    directly.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def delete(self, using=None, keep_parents=False, hard=False):
        if hard:
            return super().delete(using=using, keep_parents=keep_parents)
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])
        return 1, {self._meta.label: 1}

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])

    @property
    def is_deleted(self):
        return self.deleted_at is not None


class AIJob(BaseModel):
    """Durable record for a user-initiated asynchronous AI operation."""

    class JobType(models.TextChoices):
        REANALYZE_TREND = "reanalyze_trend", "Reanalyze trend"
        GENERATE_BRIEF = "generate_brief", "Generate brief"
        GENERATE_CONTENT = "generate_content", "Generate content"
        REFINE_CONTENT = "refine_content", "Refine content"
        CONVERT_CONTENT = "convert_content", "Convert content"

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="ai_jobs"
    )
    job_type = models.CharField(max_length=32, choices=JobType.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.QUEUED)
    payload = models.JSONField(default=dict)
    result = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    celery_task_id = models.CharField(max_length=255, blank=True)

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["created_by", "status", "-created_at"])]
