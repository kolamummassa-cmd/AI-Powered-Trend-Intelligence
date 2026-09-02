from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.ai_jobs import enqueue_ai_job
from apps.core.models import AIJob
from apps.core.serializers import AIJobSerializer


class AIJobDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        job = get_object_or_404(AIJob, id=pk, created_by=request.user)
        return Response(AIJobSerializer(job).data)


class AIJobRetryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        job = get_object_or_404(AIJob, id=pk, created_by=request.user)
        if job.status != AIJob.Status.FAILED:
            return Response({"detail": "Only failed jobs can be retried."}, status=status.HTTP_409_CONFLICT)
        job.status = AIJob.Status.QUEUED
        job.error_message = ""
        job.result = {}
        job.attempt_count = 0
        job.save(update_fields=["status", "error_message", "result", "attempt_count", "updated_at"])
        transaction.on_commit(lambda: enqueue_ai_job(job))
        return Response(AIJobSerializer(job).data, status=status.HTTP_202_ACCEPTED)
