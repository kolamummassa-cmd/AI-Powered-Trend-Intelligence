from django.contrib.auth import get_user_model

from apps.notifications.models import Notification


def notify_user(user, notification_type: str, payload: dict | None = None) -> Notification:
    return Notification.objects.create(user=user, type=notification_type, payload=payload or {})


def notify_all_users(notification_type: str, payload: dict | None = None) -> int:
    """Broadcasts one notification to every active user. There's no
    per-user trend subscription/watchlist feature yet, so a
    high-value-trend or expiring-trend alert is relevant to the whole
    user base rather than a specific subset — reconsider this the day
    a "follow this trend" feature exists.
    """
    users = get_user_model().objects.filter(is_active=True)
    Notification.objects.bulk_create(
        [Notification(user=user, type=notification_type, payload=payload or {}) for user in users]
    )
    return users.count()
