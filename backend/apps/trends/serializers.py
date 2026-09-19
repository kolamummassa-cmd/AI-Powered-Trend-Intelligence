from django.utils import timezone
from rest_framework import serializers

from apps.trend_analysis.serializers import TrendAnalysisSerializer
from apps.trends.models import Category, Trend, TrendSourceLink
from apps.trends.signal_areas import detect_signal_areas


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug")


class TrendSourceLinkSerializer(serializers.ModelSerializer):
    platform = serializers.CharField(source="platform.name")
    platform_slug = serializers.CharField(source="platform.slug")
    source_title = serializers.CharField(source="raw_signal.title")
    credibility_weight = serializers.IntegerField(source="platform.credibility_weight")
    published_at = serializers.DateTimeField(source="raw_signal.published_at")

    class Meta:
        model = TrendSourceLink
        fields = (
            "platform",
            "platform_slug",
            "source_title",
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
    signal_areas = serializers.SerializerMethodField()
    opportunity_headline = serializers.SerializerMethodField()
    founder_hook = serializers.SerializerMethodField()
    investor_hook = serializers.SerializerMethodField()
    creator_hook = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()
    what_is_happening = serializers.SerializerMethodField()
    estimated_lifespan = serializers.SerializerMethodField()
    trend_score = serializers.SerializerMethodField()
    opportunity_score = serializers.SerializerMethodField()
    evidence_score = serializers.SerializerMethodField()
    verified_source_count = serializers.SerializerMethodField()
    confidence_score = serializers.SerializerMethodField()
    analyzed_at = serializers.SerializerMethodField()
    best_audience = serializers.SerializerMethodField()
    trend_stage = serializers.SerializerMethodField()

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
            "source_excerpt",
            "summary",
            "what_is_happening",
            "status",
            "estimated_lifespan",
            "trend_score",
            "opportunity_score",
            "evidence_score",
            "verified_source_count",
            "confidence_score",
            "analyzed_at",
            "first_detected_at",
            "last_seen_at",
            "platforms",
            "source_count",
            "source_freshness",
            "signal_areas",
            # Surfaced on the card itself (not just the detail page) so the
            # feed reads like a ranked intelligence view, not a bare list.
            "best_audience",
            "trend_stage",
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

    def get_signal_areas(self, obj) -> list[str]:
        return detect_signal_areas(obj.title, self._source_summary(obj))

    def _analysis(self, obj):
        """Return only the requesting user's newest analysis for this trend."""
        analyses = getattr(obj, "user_analyses", None)
        if analyses is not None:
            return analyses[0] if analyses else None
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None
        return obj.analyses.filter(created_by=user).first()

    def _source_summary(self, obj) -> str:
        if obj.source_excerpt:
            return obj.source_excerpt
        links = list(obj.source_links.all())
        if links and getattr(links[0], "raw_signal", None):
            return links[0].raw_signal.summary or ""
        return obj.summary

    def _analysis_value(self, obj, field, default=None):
        analysis = self._analysis(obj)
        return getattr(analysis, field) if analysis else default

    def get_opportunity_headline(self, obj):
        return self._analysis_value(obj, "opportunity_headline", "")

    def get_founder_hook(self, obj):
        return self._analysis_value(obj, "founder_hook", "")

    def get_investor_hook(self, obj):
        return self._analysis_value(obj, "investor_hook", "")

    def get_creator_hook(self, obj):
        return self._analysis_value(obj, "creator_hook", "")

    def get_summary(self, obj):
        return self._source_summary(obj)

    def get_what_is_happening(self, obj):
        return self._analysis_value(obj, "what_is_happening", "")

    def get_estimated_lifespan(self, obj):
        return self._analysis_value(obj, "estimated_lifespan", "")

    def get_trend_score(self, obj):
        return self._analysis_value(obj, "trend_score")

    def get_opportunity_score(self, obj):
        return self._analysis_value(obj, "opportunity_score")

    def get_evidence_score(self, obj):
        return self._analysis_value(obj, "evidence_score")

    def get_verified_source_count(self, obj):
        return self._analysis_value(obj, "verified_source_count", 0)

    def get_confidence_score(self, obj):
        return self._analysis_value(obj, "confidence_score")

    def get_analyzed_at(self, obj):
        analysis = self._analysis(obj)
        return analysis.created_at if analysis else None

    def get_best_audience(self, obj):
        return self._analysis_value(obj, "best_audience", "")

    def get_trend_stage(self, obj):
        return self._analysis_value(obj, "trend_stage", "")


class TrendDetailSerializer(TrendListSerializer):
    source_links = TrendSourceLinkSerializer(many=True, read_only=True)
    latest_analysis = serializers.SerializerMethodField()
    # AUDIENCE RELEVANCE: how relevant this trend is to each persona —
    # grouped into one object here purely for a cleaner API shape; the
    # underlying storage is still three plain columns on Trend (see
    # that model's docstring). best_audience is a separate flat field
    # since it's a single derived label, not a per-persona score.
    audience_relevance = serializers.SerializerMethodField()
    why_spreading = serializers.SerializerMethodField()
    why_it_matters = serializers.SerializerMethodField()
    suggested_content_angle = serializers.SerializerMethodField()
    action_summary = serializers.SerializerMethodField()

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
            "evidence_summary",
            "created_at",
        )

    def get_latest_analysis(self, obj):
        # Relies on the view prefetching analyses (ordered newest-first
        # by the model's default ordering) so this doesn't cost an
        # extra query per detail request.
        analysis = self._analysis(obj)
        if analysis is None:
            return None
        return TrendAnalysisSerializer(analysis).data

    def get_audience_relevance(self, obj) -> dict | None:
        analysis = self._analysis(obj)
        if analysis is None:
            return None
        scores = {
            "content_creators": analysis.content_creator_score,
            "founders": analysis.founder_score,
            "investors": analysis.investor_score,
        }
        if all(value is None for value in scores.values()):
            return None
        return scores

    def get_why_spreading(self, obj):
        return self._analysis_value(obj, "why_spreading", "")

    def get_why_it_matters(self, obj):
        return self._analysis_value(obj, "why_it_matters", "")

    def get_suggested_content_angle(self, obj):
        return self._analysis_value(obj, "suggested_content_angle", "")

    def get_action_summary(self, obj):
        return self._analysis_value(obj, "action_summary", "")

    def get_evidence_summary(self, obj):
        return self._analysis_value(obj, "evidence_summary", "")


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
