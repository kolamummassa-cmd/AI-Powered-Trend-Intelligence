from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from ai_providers.base import AIProviderError
from apps.content_studio.models import ContentBrief, GeneratedContent
from apps.content_studio.serializers import (
    ContentBriefSerializer,
    GenerateBriefRequestSerializer,
    GenerateContentRequestSerializer,
    GeneratedContentSerializer,
)
from apps.content_studio.services import generate_brief, generate_content
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
        queryset = ContentBrief.objects.select_related("trend").prefetch_related(
            "generated_content"
        )
        trend_slug = self.request.query_params.get("trend")
        if trend_slug:
            queryset = queryset.filter(trend__slug=trend_slug)
        return queryset

    def create(self, request, *args, **kwargs):
        req = GenerateBriefRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        trend = get_object_or_404(Trend, slug=req.validated_data["trend_slug"])

        try:
            brief = generate_brief(
                trend, user=request.user, perspective=req.validated_data.get("perspective", "")
            )
        except AIProviderError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(ContentBriefSerializer(brief).data, status=status.HTTP_201_CREATED)


class ContentBriefDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ContentBriefSerializer

    def get_queryset(self):
        return ContentBrief.objects.select_related("trend").prefetch_related("generated_content")


class GeneratedContentListCreateView(generics.ListCreateAPIView):
    """GET lists content pieces (optionally filtered by ?brief=<id>
    and/or ?is_saved=true); POST generates a new one."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "ai_generation"
    serializer_class = GeneratedContentSerializer

    def get_queryset(self):
        queryset = GeneratedContent.objects.select_related("brief__trend")
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
        brief = get_object_or_404(ContentBrief, id=req.validated_data["brief_id"])

        try:
            content = generate_content(brief, req.validated_data["content_type"], user=request.user)
        except AIProviderError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(GeneratedContentSerializer(content).data, status=status.HTTP_201_CREATED)


class GeneratedContentDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve one piece, or PATCH {"is_saved": true/false} — the
    only field the API lets a client change directly (body edits go
    through the Phase 6 AI Chat refinement flow instead).
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GeneratedContentSerializer
    queryset = GeneratedContent.objects.all()
