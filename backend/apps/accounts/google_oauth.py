from django.conf import settings
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token


def verify_google_id_token(token: str) -> dict:
    """Verifies a Google-issued ID token and returns its payload.

    Raises ValueError (matching google-auth's own contract) if the
    token is invalid, expired, or wasn't issued for our client ID —
    callers turn that straight into a 400.
    """
    client_id = settings.GOOGLE_OAUTH_CLIENT_ID
    if not client_id:
        raise ValueError("Google OAuth is not configured on this server.")

    payload = google_id_token.verify_oauth2_token(
        token, google_requests.Request(), audience=client_id
    )

    if payload.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise ValueError("Invalid token issuer.")

    return payload
