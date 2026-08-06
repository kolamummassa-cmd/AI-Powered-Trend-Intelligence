from django.contrib import admin

from apps.trends.models import Category, Trend, TrendSourceLink


class TrendSourceLinkInline(admin.TabularInline):
    model = TrendSourceLink
    extra = 0
    readonly_fields = ("platform", "raw_signal", "source_url", "created_at")
    can_delete = False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)


@admin.register(Trend)
class TrendAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "status", "first_detected_at", "last_seen_at")
    list_filter = ("status", "category")
    search_fields = ("title", "summary")
    readonly_fields = ("slug", "dedup_key")
    inlines = [TrendSourceLinkInline]
