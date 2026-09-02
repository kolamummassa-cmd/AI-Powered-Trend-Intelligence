from django.urls import path

from apps.core.job_views import AIJobDetailView, AIJobRetryView

urlpatterns = [
    path("<uuid:pk>/", AIJobDetailView.as_view(), name="ai-job-detail"),
    path("<uuid:pk>/retry/", AIJobRetryView.as_view(), name="ai-job-retry"),
]
