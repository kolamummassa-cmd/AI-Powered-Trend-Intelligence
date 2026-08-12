from django.urls import path

from apps.notifications.views import MarkReadView, NotificationListView, UnreadCountView

app_name = "notifications"

urlpatterns = [
    path("", NotificationListView.as_view(), name="notification-list"),
    path("unread-count/", UnreadCountView.as_view(), name="unread-count"),
    path("mark-read/", MarkReadView.as_view(), name="mark-read"),
]
