from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.models import UserProfile, UserRole

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=10)
    password_confirm = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=UserRole.choices, required=False, default=UserRole.OTHER)

    class Meta:
        model = User
        fields = ("email", "password", "password_confirm", "role")

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        role = validated_data.pop("role", UserRole.OTHER)
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")

        user = User.objects.create_user(password=password, **validated_data)
        UserProfile.objects.create(user=user, role=role)
        return user


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Same as simplejwt's default, plus a couple of fields on the
    response so the frontend doesn't need a second request just to
    know whether the account is verified.
    """

    def validate(self, attrs):
        data = super().validate(attrs)
        data["email"] = self.user.email
        data["is_verified"] = self.user.is_verified
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)

    def validate(self, attrs):
        email = attrs["email"].lower().strip()
        user = User.objects.filter(email=email, is_verified=False).first()
        expires_at = getattr(user, "email_verification_code_expires_at", None)
        if (
            not user
            or not user.email_verification_code
            or not expires_at
            or expires_at <= timezone.now()
            or not check_password(attrs["code"], user.email_verification_code)
        ):
            raise serializers.ValidationError("This verification code is invalid or has expired.")

        attrs["user"] = user
        return attrs


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=10)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        try:
            user_id = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            raise serializers.ValidationError("Invalid reset link.")

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError("This reset link is invalid or has expired.")

        attrs["user"] = user
        return attrs


class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ("display_name", "avatar_url", "role", "preferences")


class MeSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "is_verified",
            "auth_provider",
            "timezone",
            "created_at",
            "profile",
        )
        read_only_fields = ("id", "email", "is_verified", "auth_provider", "created_at")

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if profile_data is not None:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance
