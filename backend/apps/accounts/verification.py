"""Short-lived, pre-account email-verification state."""

import hashlib
import secrets

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache


def _cache_key(email: str) -> str:
    digest = hashlib.sha256(email.lower().strip().encode()).hexdigest()
    return f"pending-signup:{digest}"


def _timeout_seconds() -> int:
    return max(1, int(getattr(settings, "EMAIL_VERIFICATION_CODE_TTL_MINUTES", 15)) * 60)


def new_verification_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def create_pending_signup(*, email: str, password: str, role: str) -> str:
    """Store only hashed, temporary sign-up data outside the User table."""

    code = new_verification_code()
    cache.set(
        _cache_key(email),
        {
            "email": email.lower().strip(),
            "password": make_password(password),
            "role": role,
            "code": make_password(code),
        },
        timeout=_timeout_seconds(),
    )
    return code


def pending_signup_for_code(*, email: str, code: str) -> dict | None:
    pending = cache.get(_cache_key(email))
    if not pending or not check_password(code, pending.get("code", "")):
        return None
    return pending


def consume_pending_signup(email: str) -> None:
    cache.delete(_cache_key(email))


def resend_pending_signup_code(email: str) -> str | None:
    pending = cache.get(_cache_key(email))
    if not pending:
        return None

    code = new_verification_code()
    pending["code"] = make_password(code)
    cache.set(_cache_key(email), pending, timeout=_timeout_seconds())
    return code
