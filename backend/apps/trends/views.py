from django.core.cache import cache
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.trends.filters import TrendFilter
from apps.trends.emails import send_trend_feedback_email
from apps.core.ai_jobs import enqueue_ai_job
from apps.core.models import AIJob
from apps.core.permissions import IsVerifiedUser, enforce_ai_generation_quota
from apps.core.serializers import AIJobSerializer
from apps.trends.throttles import TrendingTickerThrottle
from apps.trends.models import Trend
from apps.trends.serializers import (
    DashboardStatsSerializer,
    TrendDetailSerializer,
    TrendListSerializer,
)
from apps.trend_analysis.models import TrendAnalysis, TrendAnalysisFeedback
from apps.trend_analysis.serializers import TrendAnalysisFeedbackSerializer
from apps.trends.services import get_dashboard_stats


class TrendListView(generics.ListAPIView):
    """Powers the trend feed: search, category/platform/status filters,
    and ordering, all server-side so the frontend never has to
    paginate/filter a full trend list itself.
    """

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TrendFilter
    search_fields = ["title", "source_excerpt"]
    ordering_fields = [
        "first_detected_at",
        "last_seen_at",
        "title",
    ]
    ordering = ["-last_seen_at"]
    serializer_class = TrendListSerializer

    def get_queryset(self):
        user_analyses = TrendAnalysis.objects.filter(created_by=self.request.user).order_by(
            "-created_at"
        )
        return Trend.objects.select_related("category").prefetch_related(
            "source_links__platform",
            "source_links__raw_signal",
            Prefetch("analyses", queryset=user_analyses, to_attr="user_analyses"),
        )


class PublicTrendingTickerView(APIView):
    """A small, publicly-readable slice of live trend titles for the
    marketing landing page's "Trending Now" ticker — proof the engine
    is actually running, without exposing any of the authenticated
    trend detail data. Deliberately unthrottled like health_check: a
    marketing page getting hit by many anonymous visitors should
    never trip a rate limit on this.
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = [TrendingTickerThrottle]

    def get(self, request):
        cache_key = "public-trending-ticker-v1"
        titles = cache.get(cache_key)
        if titles is None:
            titles = list(
                Trend.objects.order_by("-last_seen_at").values_list("title", flat=True)[:20]
            )
            cache.set(cache_key, titles, timeout=60)
        return Response({"titles": titles})


class TrendDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TrendDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        user_analyses = TrendAnalysis.objects.filter(created_by=self.request.user).order_by(
            "-created_at"
        )
        return Trend.objects.select_related("category").prefetch_related(
            "source_links__platform",
            "source_links__raw_signal",
            Prefetch("analyses", queryset=user_analyses, to_attr="user_analyses"),
        )


class ReanalyzeTrendView(APIView):
    """User-triggered re-analysis (spec's second re-analysis trigger,
    alongside new-trend-created which already runs automatically via
    apps.trends.tasks.ingest_signal). Deliberately does not do
    staleness-based auto re-analysis — that's a separate, larger piece
    of scheduling infra not in scope here. Shares the ai_generation
    throttle scope since this is exactly as expensive as any other
    AI call.
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "ai_generation"

    def post(self, request, slug):
        IsVerifiedUser().has_permission(request, self) or self.permission_denied(
            request, message=IsVerifiedUser.message
        )
        enforce_ai_generation_quota(request.user)
        trend = get_object_or_404(Trend, slug=slug)
        job = AIJob.objects.create(
            created_by=request.user,
            job_type=AIJob.JobType.REANALYZE_TREND,
            payload={"trend_id": str(trend.id)},
        )
        transaction.on_commit(lambda: enqueue_ai_job(job))
        return Response(AIJobSerializer(job).data, status=status.HTTP_202_ACCEPTED)


class TrendAnalysisFeedbackView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        trend = get_object_or_404(Trend, slug=slug)
        analysis = TrendAnalysis.objects.filter(trend=trend, created_by=request.user).first()
        if analysis is None:
            return Response(
                {"detail": "This trend has not been analyzed yet."}, status=status.HTTP_409_CONFLICT
            )
        serializer = TrendAnalysisFeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        feedback, _ = TrendAnalysisFeedback.objects.update_or_create(
            analysis=analysis,
            created_by=request.user,
            defaults={
                "is_helpful": serializer.validated_data["is_helpful"],
                "comment": serializer.validated_data.get("comment", ""),
            },
        )
        transaction.on_commit(
            lambda: send_trend_feedback_email(
                is_helpful=feedback.is_helpful,
                comment=feedback.comment,
            )
        )
        return Response(
            TrendAnalysisFeedbackSerializer(feedback).data, status=status.HTTP_201_CREATED
        )


class DashboardStatsView(APIView):
    """Powers the Phase 4 dashboard's stat cards and platform
    distribution chart. A single aggregated payload rather than
    several small endpoints, since the dashboard always needs all of
    it at once.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = DashboardStatsSerializer(get_dashboard_stats(request.user))
        return Response(serializer.data)
