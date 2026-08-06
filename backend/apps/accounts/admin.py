from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    # Overriding almost everything here because DjangoUserAdmin assumes
    # a `username` field, which this model deliberately doesn't have.
    ordering = ("-created_at",)
    list_display = ("email", "auth_provider", "is_verified", "is_staff", "is_active", "created_at")
    list_filter = ("auth_provider", "is_verified", "is_staff", "is_active")
    search_fields = ("email",)
    readonly_fields = ("id", "created_at", "updated_at", "last_login")
    inlines = [UserProfileInline]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Status", {"fields": ("is_active", "is_verified", "auth_provider", "google_sub")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at", "deleted_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
