from django.urls import path

from apps.trends.views import TrendDetailView, TrendListView

app_name = "trends"

urlpatterns = [
    path("", TrendListView.as_view(), name="trend-list"),
    path("<slug:slug>/", TrendDetailView.as_view(), name="trend-detail"),
]
