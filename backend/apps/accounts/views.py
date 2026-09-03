import logging

from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.emails import send_password_reset_email, send_verification_email
from apps.accounts.serializers import (
    EmailTokenObtainPairSerializer,
    GoogleAuthSerializer,
    LogoutSerializer,
    MeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    VerifyEmailSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


def _tokens_for(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


REFRESH_COOKIE_NAME = "trend_intel_refresh"


def _set_refresh_cookie(response, refresh: str) -> None:
    """Stores refresh tokens outside JavaScript reach; access tokens stay short-lived."""

    response.set_cookie(
        REFRESH_COOKIE_NAME,
        refresh,
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
        path="/api/v1/auth/",
    )


def _auth_response(payload: dict, status_code: int = status.HTTP_200_OK) -> Response:
    """Returns only the short-lived access token to JavaScript."""

    refresh = payload.pop("refresh")
    response = Response(payload, status=status_code)
    _set_refresh_cookie(response, refresh)
    return response


def _blacklist_user_refresh_tokens(user) -> None:
    """Invalidates every outstanding refresh token after a password reset."""

    now = timezone.now()
    for token in OutstandingToken.objects.filter(user=user, expires_at__gt=now):
        BlacklistedToken.objects.get_or_create(token=token)


class RegisterView(generics.CreateAPIView):
    """Creates the account, sends a verification email, and logs the
    user straight in (issues tokens immediately). Verification gates
    specific actions later rather than blocking login outright — an
    unverified user shouldn't be locked out of a product whose whole
    pitch is speed.
    """

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        try:
            send_verification_email(user)
        except Exception:
            # Don't fail registration just because the email provider
            # hiccuped — the user can hit resend-verification/.
            logger.exception("Failed to send verification email to %s", user.email)

        return _auth_response(
            {
                "user": {"id": str(user.id), "email": user.email, "is_verified": user.is_verified},
                **_tokens_for(user),
            },
            status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer
    throttle_scope = "auth"

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            refresh = response.data.pop("refresh")
            _set_refresh_cookie(response, refresh)
        return response


class CookieTokenRefreshView(TokenRefreshView):
    """Refreshes an access token using the HttpOnly refresh cookie."""

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        if not data.get("refresh"):
            data["refresh"] = request.COOKIES.get(REFRESH_COOKIE_NAME, "")

        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            raise InvalidToken(exc.args[0]) from exc

        response = Response(serializer.validated_data, status=status.HTTP_200_OK)
        refresh = response.data.pop("refresh", None)
        if refresh:
            _set_refresh_cookie(response, refresh)
        return response


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        if not data.get("refresh"):
            data["refresh"] = request.COOKIES.get(REFRESH_COOKIE_NAME, "")
        serializer = LogoutSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError:
            raise ValidationError({"refresh": "Invalid or already-expired token."})
        response = Response(status=status.HTTP_205_RESET_CONTENT)
        response.delete_cookie(REFRESH_COOKIE_NAME, path="/api/v1/auth/")
        return response


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.is_verified = True
        user.email_verification_code = ""
        user.email_verification_code_expires_at = None
        user.save(
            update_fields=[
                "is_verified",
                "email_verification_code",
                "email_verification_code_expires_at",
            ]
        )
        return Response({"detail": "Email verified."})


class ResendVerificationView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower().strip()

        user = User.objects.filter(email=email, is_verified=False).first()
        if user:
            send_verification_email(user)

        # Same response whether or not the account exists / is already
        # verified — this endpoint must not leak account existence.
        return Response({"detail": "If that account needs verifying, an email is on its way."})


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower().strip()

        user = User.objects.filter(email=email).first()
        if user:
            send_password_reset_email(user)

        return Response({"detail": "If that account exists, a reset link is on its way."})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        _blacklist_user_refresh_tokens(user)
        return Response({"detail": "Password has been reset."})


class GoogleAuthView(APIView):
    """Exchanges a Google ID token (obtained client-side via Google
    Identity Services) for our own JWT pair. Creates the account on
    first sign-in; links by google_sub on subsequent ones.
    """

    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        from apps.accounts.google_oauth import verify_google_id_token

        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payload = verify_google_id_token(serializer.validated_data["id_token"])
        except ValueError as exc:
            raise ValidationError({"id_token": str(exc)})

        google_sub = payload["sub"]
        email = payload["email"].lower().strip()

        user = User.objects.filter(google_sub=google_sub).first()
        if user is None:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "auth_provider": "google",
                    "google_sub": google_sub,
                    "is_verified": bool(payload.get("email_verified", True)),
                },
            )
            if created:
                from apps.accounts.models import UserProfile

                UserProfile.objects.create(user=user, display_name=payload.get("name", ""))
            elif not user.google_sub:
                # Existing email/password account signing in with Google
                # for the first time — link it rather than erroring.
                user.google_sub = google_sub
                user.save(update_fields=["google_sub"])

        return _auth_response(
            {"user": {"id": str(user.id), "email": user.email}, **_tokens_for(user)}
        )


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = MeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
