import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.notifications.models import Notification, NotificationType
from apps.notifications.services import notify_all_users, notify_user


@pytest.fixture
def user(db):
    return User.objects.create_user(email="creator@example.com", password="a-strong-passw0rd1")


def _authed_client(user):
    token = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


@pytest.mark.django_db
class TestNotifyServices:
    def test_notify_user_creates_a_notification(self, user):
        notification = notify_user(
            user, NotificationType.GENERATION_COMPLETE, {"content_id": "abc"}
        )

        assert notification.user == user
        assert notification.type == NotificationType.GENERATION_COMPLETE
        assert notification.payload == {"content_id": "abc"}
        assert notification.read_at is None

    def test_notify_all_users_broadcasts_to_every_active_user(self, user):
        other_user = User.objects.create_user(
            email="other@example.com", password="a-strong-passw0rd1"
        )
        inactive_user = User.objects.create_user(
            email="inactive@example.com", password="a-strong-passw0rd1"
        )
        inactive_user.is_active = False
        inactive_user.save(update_fields=["is_active"])

        count = notify_all_users(NotificationType.NEW_HIGH_VALUE_TREND, {"trend_id": "xyz"})

        assert count == 2
        assert Notification.objects.filter(user=user).exists()
        assert Notification.objects.filter(user=other_user).exists()
        assert not Notification.objects.filter(user=inactive_user).exists()


@pytest.mark.django_db
class TestNotificationAPI:
    def test_list_requires_authentication(self):
        client = APIClient()
        response = client.get("/api/v1/notifications/")
        assert response.status_code == 401

    def test_list_only_returns_own_notifications(self, user):
        other_user = User.objects.create_user(
            email="other@example.com", password="a-strong-passw0rd1"
        )
        notify_user(user, NotificationType.GENERATION_COMPLETE, {})
        notify_user(other_user, NotificationType.GENERATION_COMPLETE, {})

        client = _authed_client(user)
        response = client.get("/api/v1/notifications/")

        assert response.data["count"] == 1

    def test_unread_filter(self, user):
        read_one = notify_user(user, NotificationType.GENERATION_COMPLETE, {})
        notify_user(user, NotificationType.GENERATION_COMPLETE, {})
        read_one.read_at = read_one.created_at
        read_one.save(update_fields=["read_at"])

        client = _authed_client(user)
        response = client.get("/api/v1/notifications/", {"unread": "true"})

        assert response.data["count"] == 1

    def test_unread_count(self, user):
        notify_user(user, NotificationType.GENERATION_COMPLETE, {})
        notify_user(user, NotificationType.GENERATION_COMPLETE, {})

        client = _authed_client(user)
        response = client.get("/api/v1/notifications/unread-count/")

        assert response.data["unread_count"] == 2

    def test_mark_read_marks_specific_ids(self, user):
        first = notify_user(user, NotificationType.GENERATION_COMPLETE, {})
        second = notify_user(user, NotificationType.GENERATION_COMPLETE, {})

        client = _authed_client(user)
        response = client.post(
            "/api/v1/notifications/mark-read/", {"ids": [str(first.id)]}, format="json"
        )

        assert response.data["marked"] == 1
        first.refresh_from_db()
        second.refresh_from_db()
        assert first.read_at is not None
        assert second.read_at is None

    def test_mark_read_without_ids_marks_all(self, user):
        notify_user(user, NotificationType.GENERATION_COMPLETE, {})
        notify_user(user, NotificationType.GENERATION_COMPLETE, {})

        client = _authed_client(user)
        response = client.post("/api/v1/notifications/mark-read/", {})

        assert response.data["marked"] == 2
        assert Notification.objects.filter(user=user, read_at__isnull=True).count() == 0

    def test_cannot_mark_another_users_notification_read(self, user):
        other_user = User.objects.create_user(
            email="other@example.com", password="a-strong-passw0rd1"
        )
        other_notification = notify_user(other_user, NotificationType.GENERATION_COMPLETE, {})

        client = _authed_client(user)
        response = client.post(
            "/api/v1/notifications/mark-read/",
            {"ids": [str(other_notification.id)]},
            format="json",
        )

        assert response.data["marked"] == 0
        other_notification.refresh_from_db()
        assert other_notification.read_at is None
