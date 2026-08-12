from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    """Always scoped to the requesting user — notifications are
    per-user, unlike trends which are shared platform-wide.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        unread = self.request.query_params.get("unread")
        if unread is not None and unread.lower() == "true":
            queryset = queryset.filter(read_at__isnull=True)
        return queryset


class UnreadCountView(APIView):
    """Powers the notification bell's badge count — deliberately its
    own tiny endpoint so the frontend can poll it cheaply without
    pulling the full notification list every time.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, read_at__isnull=True).count()
        return Response({"unread_count": count})


class MarkReadView(APIView):
    """POST {"ids": [...]} marks specific notifications read; POST {}
    (or omit "ids") marks every unread notification for this user read.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        queryset = Notification.objects.filter(user=request.user, read_at__isnull=True)
        ids = request.data.get("ids")
        if ids:
            queryset = queryset.filter(id__in=ids)
        marked = queryset.update(read_at=timezone.now())
        return Response({"marked": marked})
