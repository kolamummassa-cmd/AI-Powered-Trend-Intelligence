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


@admin.action(description="Mark selected sources as Kuzana core (priority 90)")
def mark_kuzana_core(modeladmin, request, queryset):
    updated = queryset.update(kuzana_priority_weight=90)
    modeladmin.message_user(request, f"Marked {updated} source(s) as Kuzana core.")


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
        "credibility_weight",
        "kuzana_priority_weight",
        "last_polled_at",
    )
    list_filter = ("is_active", "adapter_key", "kuzana_priority_weight")
    search_fields = ("name", "slug", "config")
    actions = [enable_platforms, disable_platforms, mark_kuzana_core, poll_now]


@admin.register(RawTrendSignal)
class RawTrendSignalAdmin(admin.ModelAdmin):
    list_display = ("title", "platform", "external_id", "processed_at", "created_at")
    list_filter = ("platform",)
    search_fields = ("title", "external_id")
    readonly_fields = ("raw_payload",)
