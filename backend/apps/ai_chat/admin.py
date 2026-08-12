from django.contrib import admin

from apps.ai_chat.models import AIChatMessage


@admin.register(AIChatMessage)
class AIChatMessageAdmin(admin.ModelAdmin):
    list_display = ("content", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("message", "content__body")
