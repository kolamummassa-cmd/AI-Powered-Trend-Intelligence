import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_trend_feedback_email(*, is_helpful: bool, comment: str) -> None:
    """Deliver product feedback without exposing the submitting account."""

    recipient = getattr(settings, "FEEDBACK_RECIPIENT_EMAIL", "")
    if not recipient:
        return

    sentiment = "Helpful" if is_helpful else "Needs work"
    message = (
        "New content-brief feedback\n\n"
        f"Rating: {sentiment}\n\n"
        f"Comment:\n{comment.strip() or 'No written comment was provided.'}\n\n"
        "This message intentionally does not identify the user who submitted it."
    )

    try:
        send_mail(
            subject="New content-brief feedback — TrendJack Hunter",
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[recipient],
            fail_silently=False,
        )
    except Exception:
        # Feedback is already safely stored in the database. Email delivery
        # must not turn a successful submission into an error for the user.
        logger.exception("Could not send TrendJack Hunter feedback notification")
