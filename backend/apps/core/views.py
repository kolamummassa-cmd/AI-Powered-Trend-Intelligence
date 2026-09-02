from celery import current_app
from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([])
def health_check(request):
    """Liveness/readiness probe for load balancers and deploy platforms.

    Confirms the process is up AND that it can actually reach the
    database, so a broken DB connection shows as unhealthy rather than
    the app reporting green while every real request 500s.

    Deliberately exempt from the global AnonRateThrottle (`throttle_classes`
    override to an empty list) — Render's own health checker polls this
    endpoint from one IP far more often than the 100/day anon limit
    allows. Without this, DRF starts returning 429 to Render's *own*
    monitoring requests, Render treats that as a failed health check,
    and kills a perfectly healthy instance. Real (2026-08-19) production
    incident, not a hypothetical.
    """
    db_status = "ok"
    try:
        connections["default"].cursor()
    except OperationalError:
        db_status = "unavailable"

    eager_tasks = getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False)
    redis_status = "not_required" if eager_tasks else "ok"
    broker_status = "not_required" if eager_tasks else "ok"
    if not eager_tasks:
        try:
            from redis import Redis

            Redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=1).ping()
        except Exception:
            redis_status = "unavailable"
        try:
            connection = current_app.connection_for_read()
            connection.ensure_connection(max_retries=1, interval_start=0, interval_step=0)
            connection.release()
        except Exception:
            broker_status = "unavailable"

    healthy = db_status == "ok" and redis_status != "unavailable" and broker_status != "unavailable"
    status_code = 200 if healthy else 503
    return Response(
        {
            "status": "ok" if healthy else "degraded",
            "database": db_status,
            "redis": redis_status,
            "celery_broker": broker_status,
        },
        status=status_code,
    )
