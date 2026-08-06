from django.db import connections
from django.db.utils import OperationalError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Liveness/readiness probe for load balancers and deploy platforms.

    Confirms the process is up AND that it can actually reach the
    database, so a broken DB connection shows as unhealthy rather than
    the app reporting green while every real request 500s.
    """
    db_status = "ok"
    try:
        connections["default"].cursor()
    except OperationalError:
        db_status = "unavailable"

    status_code = 200 if db_status == "ok" else 503
    return Response(
        {"status": "ok" if db_status == "ok" else "degraded", "database": db_status},
        status=status_code,
    )
