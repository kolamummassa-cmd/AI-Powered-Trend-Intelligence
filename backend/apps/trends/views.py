from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions
from rest_framework.filters import OrderingFilter, SearchFilter

from apps.trends.filters import TrendFilter
from apps.trends.models import Trend
from apps.trends.serializers import TrendDetailSerializer, TrendListSerializer


class TrendListView(generics.ListAPIView):
    """Powers the trend feed: search, category/platform/status filters,
    and ordering, all server-side so the frontend never has to
    paginate/filter a full trend list itself.
    """

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TrendFilter
    search_fields = ["title", "summary"]
    ordering_fields = ["first_detected_at", "last_seen_at", "title"]
    ordering = ["-last_seen_at"]
    serializer_class = TrendListSerializer

    def get_queryset(self):
        return Trend.objects.select_related("category").prefetch_related("source_links__platform")


class TrendDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TrendDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Trend.objects.select_related("category").prefetch_related("source_links__platform")
