import logging

from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Wraps DRF's default handler so every error response has a
    consistent shape and every unhandled exception is logged server-side
    instead of leaking a stack trace to the client.
    """
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            "error": {
                "detail": response.data.get("detail", response.data),
                "status_code": response.status_code,
            }
        }
        return response

    logger.exception("Unhandled exception in %s", context.get("view"))
    return None
