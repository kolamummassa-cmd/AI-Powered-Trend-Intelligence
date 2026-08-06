from django.contrib import admin

from apps.trend_sources.models import Platform, RawTrendSignal


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


@admin.register(RawTrendSignal)
class RawTrendSignalAdmin(admin.ModelAdmin):
    list_display = ("title", "platform", "external_id", "processed_at", "created_at")
    list_filter = ("platform",)
    search_fields = ("title", "external_id")
    readonly_fields = ("raw_payload",)
