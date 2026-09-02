from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from django.db import transaction

from apps.core.ai_jobs import enqueue_ai_job
from apps.core.models import AIJob
from apps.core.permissions import IsVerifiedUser, enforce_ai_generation_quota
from apps.core.serializers import AIJobSerializer
from apps.content_studio.models import ContentBrief, GeneratedContent
from apps.content_studio.serializers import (
    ContentBriefSerializer,
    GenerateBriefRequestSerializer,
    GenerateContentRequestSerializer,
    GeneratedContentSerializer,
)
from apps.trends.models import Trend


class ContentBriefListCreateView(generics.ListCreateAPIView):
    """GET lists briefs (optionally filtered by ?trend=<slug>); POST
    generates a brand-new one for a trend. Both share the
    ai_generation throttle scope since generation is the expensive
    path — listing briefs is comparatively rare and cheap enough that
    a shared 20/min budget is generous either way.
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "ai_generation"
    serializer_class = ContentBriefSerializer

    def get_queryset(self):
        queryset = (
            ContentBrief.objects.filter(created_by=self.request.user)
            .select_related("trend")
            .prefetch_related("generated_content")
        )
        trend_slug = self.request.query_params.get("trend")
        if trend_slug:
            queryset = queryset.filter(trend__slug=trend_slug)
        return queryset

    def create(self, request, *args, **kwargs):
        req = GenerateBriefRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        trend = get_object_or_404(Trend, slug=req.validated_data["trend_slug"])
        IsVerifiedUser().has_permission(request, self) or self.permission_denied(
            request, message=IsVerifiedUser.message
        )
        enforce_ai_generation_quota(request.user)

        job = AIJob.objects.create(
            created_by=request.user,
            job_type=AIJob.JobType.GENERATE_BRIEF,
            payload={"trend_id": str(trend.id), "perspective": req.validated_data.get("perspective", "")},
        )
        transaction.on_commit(lambda: enqueue_ai_job(job))
        return Response(AIJobSerializer(job).data, status=status.HTTP_202_ACCEPTED)


class ContentBriefDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ContentBriefSerializer

    def get_queryset(self):
        return (
            ContentBrief.objects.filter(created_by=self.request.user)
            .select_related("trend")
            .prefetch_related("generated_content")
        )

    def perform_destroy(self, instance):
        # BaseModel deletion is intentionally a soft delete. Apply the same
        # recoverable behaviour to every generated piece beneath this brief so
        # a deleted brief cannot leave items in the owner's content library.
        with transaction.atomic():
            GeneratedContent.objects.filter(brief=instance).delete()
            instance.delete()


class GeneratedContentListCreateView(generics.ListCreateAPIView):
    """GET lists content pieces (optionally filtered by ?brief=<id>
    and/or ?is_saved=true); POST generates a new one."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "ai_generation"
    serializer_class = GeneratedContentSerializer

    def get_queryset(self):
        queryset = GeneratedContent.objects.filter(created_by=self.request.user).select_related(
            "brief__trend"
        )
        brief_id = self.request.query_params.get("brief")
        if brief_id:
            queryset = queryset.filter(brief_id=brief_id)
        is_saved = self.request.query_params.get("is_saved")
        if is_saved is not None:
            queryset = queryset.filter(is_saved=is_saved.lower() == "true")
        return queryset

    def create(self, request, *args, **kwargs):
        req = GenerateContentRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        brief = get_object_or_404(
            ContentBrief, id=req.validated_data["brief_id"], created_by=request.user
        )
        IsVerifiedUser().has_permission(request, self) or self.permission_denied(
            request, message=IsVerifiedUser.message
        )
        enforce_ai_generation_quota(request.user)

        job = AIJob.objects.create(
            created_by=request.user,
            job_type=AIJob.JobType.GENERATE_CONTENT,
            payload={"brief_id": str(brief.id), "content_type": req.validated_data["content_type"]},
        )
        transaction.on_commit(lambda: enqueue_ai_job(job))
        return Response(AIJobSerializer(job).data, status=status.HTTP_202_ACCEPTED)


class GeneratedContentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve one piece, or PATCH {"is_saved": true/false} — the
    only field the API lets a client change directly (body edits go
    through the Phase 6 AI Chat refinement flow instead).
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GeneratedContentSerializer

    def get_queryset(self):
        return GeneratedContent.objects.filter(created_by=self.request.user).select_related("brief__trend")
