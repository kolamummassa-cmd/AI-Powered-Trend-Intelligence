from django.urls import path

from apps.trends.views import (
    DashboardStatsView,
    ReanalyzeTrendView,
    TrendDetailView,
    TrendListView,
)

app_name = "trends"

urlpatterns = [
    path("", TrendListView.as_view(), name="trend-list"),
    # Must come before <slug:slug>/ — otherwise "stats" matches the
    # slug pattern and never reaches this view.
    path("stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
    path("<slug:slug>/", TrendDetailView.as_view(), name="trend-detail"),
    path("<slug:slug>/reanalyze/", ReanalyzeTrendView.as_view(), name="trend-reanalyze"),
]
