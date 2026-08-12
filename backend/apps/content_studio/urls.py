from django.urls import path

from apps.content_studio.views import (
    ContentBriefDetailView,
    ContentBriefListCreateView,
    GeneratedContentDetailView,
    GeneratedContentListCreateView,
)

app_name = "content_studio"

urlpatterns = [
    path("briefs/", ContentBriefListCreateView.as_view(), name="brief-list-create"),
    path("briefs/<uuid:pk>/", ContentBriefDetailView.as_view(), name="brief-detail"),
    path("pieces/", GeneratedContentListCreateView.as_view(), name="content-list-create"),
    path("pieces/<uuid:pk>/", GeneratedContentDetailView.as_view(), name="content-detail"),
]
