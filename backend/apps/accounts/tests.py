from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core import mail
from django.core.cache import cache
from django.test import override_settings
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole

LOCMEM = override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")

VALID_PASSWORD = "a-very-strong-passw0rd"


@pytest.fixture(autouse=True)
def _reset_throttle_cache():
    # The "auth" scope throttle (10/min) uses the default cache, which
    # otherwise persists across every test in the run and starts
    # rejecting requests with 429 long before any test hits a real bug.
    cache.clear()
    yield


def _register(client, email="creator@example.com", password=VALID_PASSWORD, **extra):
    payload = {
        "email": email,
        "password": password,
        "password_confirm": password,
        "role": UserRole.CREATOR,
        **extra,
    }
    return client.post("/api/v1/auth/register/", payload, format="json")


@pytest.mark.django_db
class TestRegistration:
    def test_register_creates_user_and_profile_and_sets_refresh_cookie(self):
        client = APIClient()
        response = _register(client)

        assert response.status_code == 201
        assert "access" in response.data
        assert "refresh" not in response.data
        assert "trend_intel_refresh" in response.cookies
        assert response.cookies["trend_intel_refresh"]["httponly"]
        user = User.objects.get(email="creator@example.com")
        assert user.is_verified is False
        assert user.profile.role == UserRole.CREATOR

    def test_register_rejects_mismatched_passwords(self):
        client = APIClient()
        response = _register(client, password_confirm="something-else")
        assert response.status_code == 400

    def test_register_rejects_duplicate_email(self):
        client = APIClient()
        _register(client)
        response = _register(client)
        assert response.status_code == 400

    def test_register_rejects_weak_password(self):
        client = APIClient()
        response = _register(client, password="short", password_confirm="short")
        assert response.status_code == 400

    @LOCMEM
    def test_register_sends_verification_email(self):
        client = APIClient()
        _register(client)
        assert len(mail.outbox) == 1
        assert "verify" in mail.outbox[0].subject.lower()


@pytest.mark.django_db
class TestLogin:
    def test_login_with_correct_credentials(self):
        client = APIClient()
        _register(client)

        response = client.post(
            "/api/v1/auth/login/",
            {"email": "creator@example.com", "password": VALID_PASSWORD},
            format="json",
        )
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" not in response.data
        assert "trend_intel_refresh" in response.cookies
        assert response.data["email"] == "creator@example.com"
        assert response.data["is_verified"] is False

    def test_login_with_wrong_password_is_rejected(self):
        client = APIClient()
        _register(client)

        response = client.post(
            "/api/v1/auth/login/",
            {"email": "creator@example.com", "password": "wrong-password"},
            format="json",
        )
        assert response.status_code == 401


@pytest.mark.django_db
class TestTokenLifecycle:
    def test_refresh_issues_a_new_access_token(self):
        client = APIClient()
        register_response = _register(client)
        refresh = register_response.cookies["trend_intel_refresh"].value
        client.cookies["trend_intel_refresh"] = refresh

        response = client.post("/api/v1/auth/token/refresh/", format="json")
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" not in response.data

    def test_logout_blacklists_the_refresh_token(self):
        client = APIClient()
        register_response = _register(client)
        access = register_response.data["access"]
        refresh = register_response.cookies["trend_intel_refresh"].value

        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        logout_response = client.post("/api/v1/auth/logout/", format="json")
        assert logout_response.status_code == 205

        refresh_response = client.post(
            "/api/v1/auth/token/refresh/", {"refresh": refresh}, format="json"
        )
        assert refresh_response.status_code == 401

    def test_logout_requires_authentication(self):
        client = APIClient()
        response = client.post("/api/v1/auth/logout/", format="json")
        assert response.status_code == 401


@pytest.mark.django_db
class TestEmailVerification:
    def test_valid_code_marks_user_verified(self):
        client = APIClient()
        _register(client)
        user = User.objects.get(email="creator@example.com")
        user.email_verification_code = make_password("123456")
        user.email_verification_code_expires_at = timezone.now() + timedelta(minutes=15)
        user.save(update_fields=["email_verification_code", "email_verification_code_expires_at"])

        response = client.post(
            "/api/v1/auth/verify-email/", {"email": user.email, "code": "123456"}, format="json"
        )
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.is_verified is True

    def test_invalid_code_is_rejected(self):
        client = APIClient()
        _register(client)
        user = User.objects.get(email="creator@example.com")

        response = client.post(
            "/api/v1/auth/verify-email/", {"email": user.email, "code": "000000"}, format="json"
        )
        assert response.status_code == 400
        user.refresh_from_db()
        assert user.is_verified is False

    def test_resend_verification_never_reveals_account_existence(self):
        client = APIClient()
        response = client.post(
            "/api/v1/auth/resend-verification/",
            {"email": "nobody@example.com"},
            format="json",
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestPasswordReset:
    @LOCMEM
    def test_full_reset_flow(self):
        client = APIClient()
        _register(client)
        mail.outbox.clear()  # ignore the verification email sent by registration

        request_response = client.post(
            "/api/v1/auth/password-reset/", {"email": "creator@example.com"}, format="json"
        )
        assert request_response.status_code == 200
        assert len(mail.outbox) == 1

        # Pull the token the same way the serializer would validate it,
        # rather than parsing it out of the email body.
        from django.contrib.auth.tokens import default_token_generator

        user = User.objects.get(email="creator@example.com")
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        confirm_response = client.post(
            "/api/v1/auth/password-reset/confirm/",
            {"uid": uid, "token": token, "new_password": "a-brand-new-passw0rd"},
            format="json",
        )
        assert confirm_response.status_code == 200

        login_response = client.post(
            "/api/v1/auth/login/",
            {"email": "creator@example.com", "password": "a-brand-new-passw0rd"},
            format="json",
        )
        assert login_response.status_code == 200

    def test_password_reset_blacklists_existing_refresh_tokens(self):
        client = APIClient()
        register_response = _register(client)
        refresh = register_response.cookies["trend_intel_refresh"].value
        user = User.objects.get(email="creator@example.com")

        from django.contrib.auth.tokens import default_token_generator

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        response = client.post(
            "/api/v1/auth/password-reset/confirm/",
            {"uid": uid, "token": token, "new_password": "a-brand-new-passw0rd"},
            format="json",
        )
        assert response.status_code == 200

        refresh_response = client.post(
            "/api/v1/auth/token/refresh/", {"refresh": refresh}, format="json"
        )
        assert refresh_response.status_code == 401

    def test_reset_request_never_reveals_account_existence(self):
        client = APIClient()
        response = client.post(
            "/api/v1/auth/password-reset/", {"email": "nobody@example.com"}, format="json"
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestGoogleAuth:
    @patch("apps.accounts.google_oauth.verify_google_id_token")
    def test_creates_a_new_user_on_first_sign_in(self, mock_verify):
        mock_verify.return_value = {
            "sub": "google-subject-123",
            "email": "founder@example.com",
            "email_verified": True,
            "name": "A Founder",
        }

        client = APIClient()
        response = client.post("/api/v1/auth/google/", {"id_token": "fake-token"}, format="json")

        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" not in response.data
        assert "trend_intel_refresh" in response.cookies
        user = User.objects.get(email="founder@example.com")
        assert user.google_sub == "google-subject-123"
        assert user.is_verified is True
        assert user.profile.display_name == "A Founder"

    @patch("apps.accounts.google_oauth.verify_google_id_token")
    def test_second_sign_in_reuses_the_same_account(self, mock_verify):
        mock_verify.return_value = {
            "sub": "google-subject-123",
            "email": "founder@example.com",
            "email_verified": True,
            "name": "A Founder",
        }
        client = APIClient()
        client.post("/api/v1/auth/google/", {"id_token": "fake-token"}, format="json")
        client.post("/api/v1/auth/google/", {"id_token": "fake-token"}, format="json")

        assert User.objects.filter(email="founder@example.com").count() == 1

    @patch("apps.accounts.google_oauth.verify_google_id_token")
    def test_invalid_google_token_returns_400(self, mock_verify):
        mock_verify.side_effect = ValueError("Token expired")
        client = APIClient()
        response = client.post("/api/v1/auth/google/", {"id_token": "fake-token"}, format="json")
        assert response.status_code == 400


@pytest.mark.django_db
class TestMeEndpoint:
    def _authed_client(self):
        client = APIClient()
        register_response = _register(client)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {register_response.data['access']}")
        return client

    def test_requires_authentication(self):
        client = APIClient()
        response = client.get("/api/v1/auth/me/")
        assert response.status_code == 401

    def test_returns_current_user_and_profile(self):
        client = self._authed_client()
        response = client.get("/api/v1/auth/me/")
        assert response.status_code == 200
        assert response.data["email"] == "creator@example.com"
        assert response.data["profile"]["role"] == UserRole.CREATOR

    def test_updates_profile_and_timezone(self):
        client = self._authed_client()
        response = client.patch(
            "/api/v1/auth/me/",
            {"timezone": "Africa/Nairobi", "profile": {"display_name": "Kolamu"}},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["timezone"] == "Africa/Nairobi"
        assert response.data["profile"]["display_name"] == "Kolamu"
