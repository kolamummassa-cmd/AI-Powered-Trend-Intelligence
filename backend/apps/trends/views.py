from django.db.models import Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.trends.filters import AUDIENCE_RELEVANCE_THRESHOLD, TrendFilter
from apps.trends.models import Trend
from apps.trends.serializers import (
    DashboardStatsSerializer,
    TrendDetailSerializer,
    TrendListSerializer,
)
from apps.trends.services import get_dashboard_stats


class TrendListView(generics.ListAPIView):
    """Powers the trend feed: search, category/platform/status filters,
    and ordering, all server-side so the frontend never has to
    paginate/filter a full trend list itself.
    """

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TrendFilter
    search_fields = ["title", "summary"]
    ordering_fields = [
        "first_detected_at",
        "last_seen_at",
        "title",
        "trend_score",
        "opportunity_score",
    ]
    ordering = ["-last_seen_at"]
    serializer_class = TrendListSerializer

    def get_queryset(self):
        queryset = Trend.objects.select_related("category").prefetch_related(
            "source_links__platform"
        )
        # The point of trend collection is surfacing meaningful
        # opportunities, not every article that got ingested — once a
        # trend has been analyzed, hide it from the default feed unless
        # it clears the relevance bar for at least one audience. Trends
        # still awaiting analysis stay visible (nothing to filter on
        # yet), and ?include_low_relevance=true opts back into the full
        # list for admin/debugging use.
        if self.request.query_params.get("include_low_relevance") != "true":
            queryset = queryset.filter(
                Q(analyzed_at__isnull=True)
                | Q(content_creator_score__gte=AUDIENCE_RELEVANCE_THRESHOLD)
                | Q(founder_score__gte=AUDIENCE_RELEVANCE_THRESHOLD)
                | Q(investor_score__gte=AUDIENCE_RELEVANCE_THRESHOLD)
            )
        return queryset


class TrendDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TrendDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Trend.objects.select_related("category").prefetch_related(
            "source_links__platform", "analyses"
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
        from apps.trend_analysis.tasks import analyze_trend_task

        trend = get_object_or_404(Trend, slug=slug)
        analyze_trend_task.delay(str(trend.id))
        return Response(
            {"detail": "Re-analysis queued."},
            status=status.HTTP_202_ACCEPTED,
        )


class DashboardStatsView(APIView):
    """Powers the Phase 4 dashboard's stat cards and platform
    distribution chart. A single aggregated payload rather than
    several small endpoints, since the dashboard always needs all of
    it at once.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = DashboardStatsSerializer(get_dashboard_stats())
        return Response(serializer.data)
