import logging

from celery import shared_task
from django.contrib.auth import get_user_model

from ai_providers.base import AIProviderError
from apps.ai_chat.services import convert_for_platform, refine_content
from apps.content_studio.models import ContentBrief, GeneratedContent
from apps.content_studio.services import generate_brief, generate_content
from apps.core.models import AIJob
from apps.core.permissions import record_ai_generation
from apps.notifications.models import NotificationType
from apps.notifications.services import notify_user
from apps.trend_analysis.services import analyze_trend
from apps.trends.models import Trend

logger = logging.getLogger(__name__)


def enqueue_ai_job(job):
    """Queue a saved job only after its database transaction commits."""
    task = run_ai_job.delay(str(job.id))
    AIJob.objects.filter(id=job.id).update(celery_task_id=task.id)


def _is_transient_error(exc):
    """Retry transport/provider availability failures, never bad inputs or model output."""
    cause = exc.__cause__ or exc
    name = type(cause).__name__.lower()
    status_code = getattr(cause, "status_code", None)
    return (
        any(token in name for token in ("connection", "timeout", "ratelimit", "internalserver"))
        or status_code == 429
        or (isinstance(status_code, int) and status_code >= 500)
    )


def _job_objects(job):
    payload = job.payload
    if job.job_type == AIJob.JobType.REANALYZE_TREND:
        return Trend.objects.get(id=payload["trend_id"]), None
    if job.job_type == AIJob.JobType.GENERATE_BRIEF:
        return Trend.objects.get(id=payload["trend_id"]), None
    if job.job_type == AIJob.JobType.GENERATE_CONTENT:
        return ContentBrief.objects.select_related("trend").get(id=payload["brief_id"]), None
    return GeneratedContent.objects.select_related("brief__trend").get(id=payload["content_id"]), None


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def run_ai_job(self, job_id):
    try:
        job = AIJob.objects.select_related("created_by").get(id=job_id)
    except AIJob.DoesNotExist:
        logger.warning("AI job %s no longer exists", job_id)
        return {"job": job_id, "error": "not found"}

    if job.status == AIJob.Status.COMPLETED:
        return job.result

    job.status = AIJob.Status.RUNNING
    job.attempt_count = self.request.retries + 1
    job.error_message = ""
    job.save(update_fields=["status", "attempt_count", "error_message", "updated_at"])

    try:
        subject, _ = _job_objects(job)
        user = job.created_by
        if job.job_type == AIJob.JobType.REANALYZE_TREND:
            analysis = analyze_trend(subject)
            result = {"trend_id": str(subject.id), "trend_slug": subject.slug, "analysis_id": str(analysis.id)}
        elif job.job_type == AIJob.JobType.GENERATE_BRIEF:
            brief = generate_brief(subject, user=user, perspective=job.payload.get("perspective", ""))
            result = {"brief_id": str(brief.id), "trend_slug": subject.slug}
        elif job.job_type == AIJob.JobType.GENERATE_CONTENT:
            content = generate_content(subject, job.payload["content_type"], user=user)
            result = {"content_id": str(content.id), "brief_id": str(subject.id)}
        elif job.job_type == AIJob.JobType.REFINE_CONTENT:
            message = refine_content(subject, job.payload["instruction"], user=user)
            result = {"message_id": str(message.id), "content_id": str(subject.id)}
        elif job.job_type == AIJob.JobType.CONVERT_CONTENT:
            message = convert_for_platform(subject, job.payload["platform"], user=user)
            result = {"message_id": str(message.id), "content_id": str(subject.id)}
        else:
            raise AIProviderError("Unsupported AI job type.")
    except AIProviderError as exc:
        if _is_transient_error(exc) and self.request.retries < self.max_retries:
            job.status = AIJob.Status.QUEUED
            job.error_message = "Temporary provider issue; retrying automatically."
            job.save(update_fields=["status", "error_message", "updated_at"])
            raise self.retry(exc=exc, countdown=min(30 * (2 ** self.request.retries), 300))
        job.status = AIJob.Status.FAILED
        job.error_message = str(exc)
        job.save(update_fields=["status", "error_message", "updated_at"])
        return {"job": str(job.id), "error": str(exc)}
    except (Trend.DoesNotExist, ContentBrief.DoesNotExist, GeneratedContent.DoesNotExist, KeyError) as exc:
        job.status = AIJob.Status.FAILED
        job.error_message = "The source item for this job is no longer available."
        job.save(update_fields=["status", "error_message", "updated_at"])
        return {"job": str(job.id), "error": str(exc)}

    job.status = AIJob.Status.COMPLETED
    job.result = result
    job.error_message = ""
    job.save(update_fields=["status", "result", "error_message", "updated_at"])
    if user is not None:
        record_ai_generation(user)
        notify_user(user, NotificationType.GENERATION_COMPLETE, result)
    return result
