import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

def _frontend_url(path: str) -> str:
    base = getattr(settings, "FRONTEND_URL", "http://localhost:3000").rstrip("/")
    return f"{base}{path}"


def send_verification_email(user) -> None:
    code = f"{secrets.randbelow(1_000_000):06d}"
    user.email_verification_code = make_password(code)
    user.email_verification_code_expires_at = timezone.now() + timedelta(
        minutes=getattr(settings, "EMAIL_VERIFICATION_CODE_TTL_MINUTES", 15)
    )
    user.save(update_fields=["email_verification_code", "email_verification_code_expires_at"])

    send_mail(
        subject="Verify your email — AI-Powered Trend Intelligence",
        message=(
            f"Hi,\n\nYour Kuzana verification code is: {code}\n\n"
            "Enter this six-digit code in Kuzana within 15 minutes. "
            "If you didn't create this account, you can ignore this email."
        ),
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_password_reset_email(user) -> None:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = _frontend_url(f"/reset-password?uid={uid}&token={token}")

    send_mail(
        subject="Reset your password — AI-Powered Trend Intelligence",
        message=(
            f"Hi,\n\nReset your password here:\n{link}\n\n"
            "If you didn't request this, you can safely ignore this email — "
            "your password will not change."
        ),
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[user.email],
        fail_silently=False,
    )
