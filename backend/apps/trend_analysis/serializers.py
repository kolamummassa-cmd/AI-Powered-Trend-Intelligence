from rest_framework import serializers

from apps.trend_analysis.models import TrendAnalysis


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
            "model_used",
            "created_at",
        )
