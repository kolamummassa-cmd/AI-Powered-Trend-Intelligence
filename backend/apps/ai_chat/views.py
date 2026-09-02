from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db import transaction

from apps.core.ai_jobs import enqueue_ai_job
from apps.core.models import AIJob
from apps.core.permissions import IsVerifiedUser, enforce_ai_generation_quota
from apps.core.serializers import AIJobSerializer
from apps.ai_chat.models import AIChatMessage
from apps.ai_chat.serializers import (
    AIChatMessageSerializer,
    ConvertContentRequestSerializer,
    RefineContentRequestSerializer,
)
from apps.content_studio.models import GeneratedContent


class AIChatMessageListView(generics.ListAPIView):
    """Full thread for one content piece, chronological (see
    AIChatMessage.Meta.ordering) — filter with ?content=<id>.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AIChatMessageSerializer

    def get_queryset(self):
        queryset = AIChatMessage.objects.filter(
            content__created_by=self.request.user
        ).select_related("content")
        content_id = self.request.query_params.get("content")
        if content_id:
            queryset = queryset.filter(content_id=content_id)
        return queryset


class RefineContentView(APIView):
    """One free-typed refinement instruction against a content piece.
    Returns the assistant's reply message; the content piece's body is
    updated in place as a side effect (see apps.ai_chat.services).
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "ai_generation"

    def post(self, request):
        req = RefineContentRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        content = get_object_or_404(
            GeneratedContent, id=req.validated_data["content_id"], created_by=request.user
        )
        IsVerifiedUser().has_permission(request, self) or self.permission_denied(
            request, message=IsVerifiedUser.message
        )
        enforce_ai_generation_quota(request.user)

        job = AIJob.objects.create(
            created_by=request.user,
            job_type=AIJob.JobType.REFINE_CONTENT,
            payload={"content_id": str(content.id), "instruction": req.validated_data["instruction"]},
        )
        transaction.on_commit(lambda: enqueue_ai_job(job))
        return Response(AIJobSerializer(job).data, status=status.HTTP_202_ACCEPTED)


class ConvertContentView(APIView):
    """A one-click platform-conversion action — internally just a
    canned instruction through the same refinement path.
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "ai_generation"

    def post(self, request):
        req = ConvertContentRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        content = get_object_or_404(
            GeneratedContent, id=req.validated_data["content_id"], created_by=request.user
        )
        IsVerifiedUser().has_permission(request, self) or self.permission_denied(
            request, message=IsVerifiedUser.message
        )
        enforce_ai_generation_quota(request.user)

        job = AIJob.objects.create(
            created_by=request.user,
            job_type=AIJob.JobType.CONVERT_CONTENT,
            payload={"content_id": str(content.id), "platform": req.validated_data["platform"]},
        )
        transaction.on_commit(lambda: enqueue_ai_job(job))
        return Response(AIJobSerializer(job).data, status=status.HTTP_202_ACCEPTED)
