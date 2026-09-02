from rest_framework import serializers

from apps.trend_analysis.models import TrendAnalysis, TrendAnalysisFeedback


class TrendAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrendAnalysis
        fields = (
            "business_relevance",
            "founder_relevance",
            "entrepreneurship_relevance",
            "ai_relevance",
            "trend_score",
            "opportunity_score",
            "confidence_score",
            "content_creator_score",
            "founder_score",
            "investor_score",
            "best_audience",
            "why_it_matters",
            "what_is_happening",
            "trend_stage",
            "suggested_content_angle",
            "kuzana_relevance_score",
            "kuzana_relevance_reason",
            "kuzana_theme",
            "kuzana_geo_relevance",
            "kuzana_audience",
            "kuzana_content_format",
            "kuzana_practical_takeaway",
            "opportunity_headline",
            "founder_hook",
            "investor_hook",
            "creator_hook",
            "model_used",
            "created_at",
        )


class TrendAnalysisFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrendAnalysisFeedback
        fields = ("id", "analysis", "is_helpful", "comment", "created_at")
        read_only_fields = ("id", "analysis", "created_at")
