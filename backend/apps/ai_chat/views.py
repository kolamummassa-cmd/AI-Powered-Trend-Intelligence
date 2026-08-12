from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_providers.base import AIProviderError
from apps.ai_chat.models import AIChatMessage
from apps.ai_chat.serializers import (
    AIChatMessageSerializer,
    ConvertContentRequestSerializer,
    RefineContentRequestSerializer,
)
from apps.ai_chat.services import convert_for_platform, refine_content
from apps.content_studio.models import GeneratedContent


class AIChatMessageListView(generics.ListAPIView):
    """Full thread for one content piece, chronological (see
    AIChatMessage.Meta.ordering) — filter with ?content=<id>.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AIChatMessageSerializer

    def get_queryset(self):
        queryset = AIChatMessage.objects.select_related("content")
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
        content = get_object_or_404(GeneratedContent, id=req.validated_data["content_id"])

        try:
            message = refine_content(content, req.validated_data["instruction"], user=request.user)
        except AIProviderError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(AIChatMessageSerializer(message).data, status=status.HTTP_201_CREATED)


class ConvertContentView(APIView):
    """A one-click platform-conversion action — internally just a
    canned instruction through the same refinement path.
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "ai_generation"

    def post(self, request):
        req = ConvertContentRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        content = get_object_or_404(GeneratedContent, id=req.validated_data["content_id"])

        try:
            message = convert_for_platform(
                content, req.validated_data["platform"], user=request.user
            )
        except AIProviderError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(AIChatMessageSerializer(message).data, status=status.HTTP_201_CREATED)
