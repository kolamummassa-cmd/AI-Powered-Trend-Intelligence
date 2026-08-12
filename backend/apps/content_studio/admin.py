from django.contrib import admin

from apps.content_studio.models import ContentBrief, GeneratedContent


@admin.register(ContentBrief)
class ContentBriefAdmin(admin.ModelAdmin):
    list_display = ("trend", "created_by", "model_used", "created_at")
    search_fields = ("trend__title",)


@admin.register(GeneratedContent)
class GeneratedContentAdmin(admin.ModelAdmin):
    list_display = ("brief", "content_type", "version", "is_saved", "created_by", "created_at")
    list_filter = ("content_type", "is_saved")
    search_fields = ("brief__trend__title", "body")
