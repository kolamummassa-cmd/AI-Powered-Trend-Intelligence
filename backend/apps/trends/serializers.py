from django.utils import timezone
from rest_framework import serializers

from apps.trend_analysis.serializers import TrendAnalysisSerializer
from apps.trends.models import Category, Trend, TrendSourceLink


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug")


class TrendSourceLinkSerializer(serializers.ModelSerializer):
    platform = serializers.CharField(source="platform.name")
    platform_slug = serializers.CharField(source="platform.slug")
    credibility_weight = serializers.IntegerField(source="platform.credibility_weight")
    published_at = serializers.DateTimeField(source="raw_signal.published_at")

    class Meta:
        model = TrendSourceLink
        fields = (
            "platform",
            "platform_slug",
            "source_url",
            "published_at",
            "credibility_weight",
            "relevance_score",
            "created_at",
        )


class TrendListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    platforms = serializers.SerializerMethodField()
    source_count = serializers.SerializerMethodField()
    source_freshness = serializers.SerializerMethodField()

    class Meta:
        model = Trend
        fields = (
            "id",
            "title",
            "opportunity_headline",
            "founder_hook",
            "investor_hook",
            "creator_hook",
            "slug",
            "category",
            "summary",
            "status",
            "estimated_lifespan",
            "trend_score",
            "opportunity_score",
            "confidence_score",
            "analyzed_at",
            "first_detected_at",
            "last_seen_at",
            "platforms",
            "source_count",
            "source_freshness",
            # Surfaced on the card itself (not just the detail page) so the
            # feed reads like a ranked intelligence view, not a bare list.
            "best_audience",
            "trend_stage",
            "kuzana_relevance_score",
            "kuzana_theme",
            "kuzana_geo_relevance",
        )

    def get_platforms(self, obj) -> list[str]:
        # Relies on the view prefetching source_links__platform — avoids
        # an extra query per row when listing many trends.
        return sorted({link.platform.slug for link in obj.source_links.all()})

    def get_source_count(self, obj) -> int:
        return len(obj.source_links.all())

    def get_source_freshness(self, obj) -> str:
        age_hours = (timezone.now() - obj.last_seen_at).total_seconds() / 3600
        if age_hours < 24:
            return "fresh"
        if age_hours < 24 * 7:
            return "recent"
        return "aging"


class TrendDetailSerializer(TrendListSerializer):
    source_links = TrendSourceLinkSerializer(many=True, read_only=True)
    latest_analysis = serializers.SerializerMethodField()
    # AUDIENCE RELEVANCE: how relevant this trend is to each persona —
    # grouped into one object here purely for a cleaner API shape; the
    # underlying storage is still three plain columns on Trend (see
    # that model's docstring). best_audience is a separate flat field
    # since it's a single derived label, not a per-persona score.
    audience_relevance = serializers.SerializerMethodField()

    class Meta(TrendListSerializer.Meta):
        fields = TrendListSerializer.Meta.fields + (
            "why_spreading",
            "source_links",
            "latest_analysis",
            "audience_relevance",
            # best_audience and trend_stage are now on TrendListSerializer
            # itself (see its Meta.fields) — not repeated here.
            "why_it_matters",
            "what_is_happening",
            "suggested_content_angle",
            "action_summary",
            "kuzana_relevance_reason",
            "kuzana_audience",
            "kuzana_content_format",
            "kuzana_practical_takeaway",
            "created_at",
        )

    def get_latest_analysis(self, obj):
        # Relies on the view prefetching analyses (ordered newest-first
        # by the model's default ordering) so this doesn't cost an
        # extra query per detail request.
        analyses = list(obj.analyses.all())
        if not analyses:
            return None
        return TrendAnalysisSerializer(analyses[0]).data

    def get_audience_relevance(self, obj) -> dict | None:
        scores = {
            "content_creators": obj.content_creator_score,
            "founders": obj.founder_score,
            "investors": obj.investor_score,
        }
        if all(value is None for value in scores.values()):
            return None
        return scores


class PlatformDistributionSerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField()
    trend_count = serializers.IntegerField()
    kuzana_priority_weight = serializers.IntegerField()


class DashboardStatsSerializer(serializers.Serializer):
    total_trends = serializers.IntegerField()
    active_trends = serializers.IntegerField()
    expiring_trends = serializers.IntegerField()
    new_today = serializers.IntegerField()
    high_priority_trends = serializers.IntegerField()
    analyzed_trends = serializers.IntegerField()
    platform_distribution = PlatformDistributionSerializer(many=True)
