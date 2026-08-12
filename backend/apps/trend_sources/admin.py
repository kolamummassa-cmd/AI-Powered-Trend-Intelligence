from django.contrib import admin

from apps.trend_sources.models import Platform, RawTrendSignal
from apps.trend_sources.tasks import poll_platform


@admin.action(description="Enable selected platforms")
def enable_platforms(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(request, f"Enabled {updated} platform(s).")


@admin.action(description="Disable selected platforms")
def disable_platforms(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(request, f"Disabled {updated} platform(s).")


@admin.action(description="Poll now")
def poll_now(modeladmin, request, queryset):
    count = 0
    for platform in queryset:
        poll_platform.delay(str(platform.id))
        count += 1
    modeladmin.message_user(request, f"Queued an immediate poll for {count} platform(s).")


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "adapter_key",
        "is_active",
        "poll_interval_minutes",
        "last_polled_at",
    )
    list_filter = ("is_active", "adapter_key")
    search_fields = ("name", "slug")
    actions = [enable_platforms, disable_platforms, poll_now]


@admin.register(RawTrendSignal)
class RawTrendSignalAdmin(admin.ModelAdmin):
    list_display = ("title", "platform", "external_id", "processed_at", "created_at")
    list_filter = ("platform",)
    search_fields = ("title", "external_id")
    readonly_fields = ("raw_payload",)
