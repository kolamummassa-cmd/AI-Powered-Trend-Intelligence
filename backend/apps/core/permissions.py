"""Reusable API permissions and guardrails for customer-facing actions."""

from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from rest_framework.exceptions import Throttled
from rest_framework.permissions import BasePermission


class IsVerifiedUser(BasePermission):
    """Allows expensive customer actions only after email verification."""

    message = "Verify your email before generating or refining AI content."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_verified)


def _daily_quota_key(user_id: str) -> str:
    return f"ai-generation:{user_id}:{timezone.localdate().isoformat()}"


def _seconds_until_next_day() -> int:
    now = timezone.now()
    next_day = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(1, int((next_day - now).total_seconds()))


def enforce_ai_generation_quota(user) -> None:
    """Raises a 429 before an AI request once the daily allowance is used."""

    limit = settings.AI_GENERATION_DAILY_LIMIT
    if limit <= 0:
        return

    count = cache.get(_daily_quota_key(str(user.id)), 0)
    if count >= limit:
        raise Throttled(
            wait=_seconds_until_next_day(),
            detail="Daily AI generation limit reached. Try again tomorrow.",
        )


def record_ai_generation(user) -> None:
    """Records only successful AI work, so provider failures do not spend allowance."""

    if settings.AI_GENERATION_DAILY_LIMIT <= 0:
        return

    key = _daily_quota_key(str(user.id))
    timeout = _seconds_until_next_day()
    cache.add(key, 0, timeout=timeout)
    try:
        cache.incr(key)
    except ValueError:  # A cache eviction between add() and incr() is harmless.
        cache.set(key, 1, timeout=timeout)
