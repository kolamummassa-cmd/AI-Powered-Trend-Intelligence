from django.contrib import admin

from apps.trend_analysis.models import TrendAnalysis


@admin.register(TrendAnalysis)
class TrendAnalysisAdmin(admin.ModelAdmin):
    list_display = (
        "trend",
        "trend_score",
        "opportunity_score",
        "confidence_score",
        "model_used",
        "created_at",
    )
    list_filter = ("model_used", "prompt_version")
    search_fields = ("trend__title",)
    readonly_fields = (
        "business_relevance",
        "founder_relevance",
        "entrepreneurship_relevance",
        "ai_relevance",
    )
