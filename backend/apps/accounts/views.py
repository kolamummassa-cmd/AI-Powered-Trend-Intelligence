import logging

from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

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

        return Response(
            {
                "user": {"id": str(user.id), "email": user.email, "is_verified": user.is_verified},
                **_tokens_for(user),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer
    throttle_scope = "auth"

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError:
            raise ValidationError({"refresh": "Invalid or already-expired token."})
        return Response(status=status.HTTP_205_RESET_CONTENT)


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.is_verified = True
        user.save(update_fields=["is_verified"])
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

        return Response({"user": {"id": str(user.id), "email": user.email}, **_tokens_for(user)})


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = MeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
