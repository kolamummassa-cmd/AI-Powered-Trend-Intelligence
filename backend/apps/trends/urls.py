from django.urls import path

from apps.trends.views import (
    DashboardStatsView,
    PublicTrendingTickerView,
    ReanalyzeTrendView,
    TrendAnalysisFeedbackView,
    TrendDetailView,
    TrendListView,
)

app_name = "trends"

urlpatterns = [
    path("", TrendListView.as_view(), name="trend-list"),
    # Must come before <slug:slug>/ — otherwise "stats"/"trending-ticker"
    # would match the slug pattern and never reach these views.
    path("stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
    path("trending-ticker/", PublicTrendingTickerView.as_view(), name="trending-ticker"),
    path("<slug:slug>/feedback/", TrendAnalysisFeedbackView.as_view(), name="trend-feedback"),
    path("<slug:slug>/", TrendDetailView.as_view(), name="trend-detail"),
    path("<slug:slug>/reanalyze/", ReanalyzeTrendView.as_view(), name="trend-reanalyze"),
]
