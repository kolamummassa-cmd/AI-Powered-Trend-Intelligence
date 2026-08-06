import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.accounts.managers import UserManager
from apps.core.models import BaseModel


class AuthProvider(models.TextChoices):
    EMAIL = "email", "Email"
    GOOGLE = "google", "Google"


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user: email is the identifier, there is no username.

    Soft delete + audit timestamps are hand-rolled here (rather than
    inheriting BaseModel) because AbstractBaseUser already establishes
    the model's identity/manager wiring and mixing two managers
    silently is a common source of "why did that user disappear"
    bugs. UserManager (managers.py) implements the same
    filter-out-deleted behaviour as BaseModel's SoftDeleteManager.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    auth_provider = models.CharField(
        max_length=20, choices=AuthProvider.choices, default=AuthProvider.EMAIL
    )
    google_sub = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="Google's stable subject identifier, for accounts linked via Google OAuth.",
    )

    timezone = models.CharField(max_length=64, default="UTC")

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    def delete(self, using=None, keep_parents=False, hard=False):
        if hard:
            return super().delete(using=using, keep_parents=keep_parents)
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save(update_fields=["deleted_at", "is_active"])
        return 1, {self._meta.label: 1}

    @property
    def is_deleted(self):
        return self.deleted_at is not None


class UserRole(models.TextChoices):
    CREATOR = "creator", "Content Creator"
    FOUNDER = "founder", "Startup Founder"
    AGENCY = "agency", "Marketing Agency"
    COACH = "coach", "Business Coach"
    COMMUNITY = "community", "Entrepreneurship Community / Accelerator"
    OTHER = "other", "Other"


class UserProfile(BaseModel):
    """Everything about a user that isn't strictly auth — kept in its
    own table (rather than bloating User) so auth queries stay cheap
    and profile data can evolve independently.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=100, blank=True)
    avatar_url = models.URLField(blank=True)  # Cloudinary URL once image upload lands
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.OTHER)
    preferences = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.display_name or self.user.email
