from rest_framework import serializers

from apps.content_studio.models import ContentBrief, ContentType, GeneratedContent
from apps.trends.models import AudienceType


class GeneratedContentSerializer(serializers.ModelSerializer):
    trend_title = serializers.CharField(source="brief.trend.title", read_only=True)
    trend_slug = serializers.CharField(source="brief.trend.slug", read_only=True)
    perspective = serializers.CharField(source="brief.perspective", read_only=True)
    brief_context = serializers.CharField(source="brief.content_angle", read_only=True)

    class Meta:
        model = GeneratedContent
        fields = (
            "id",
            "brief",
            "trend_title",
            "trend_slug",
            "perspective",
            "brief_context",
            "content_type",
            "version",
            "is_saved",
            "model_used",
            "created_at",
        )
        # is_saved is the only field a client ever updates directly —
        # everything else is produced by the generation service.
        read_only_fields = (
            "id",
            "brief",
            "content_type",
            "body",
            "version",
            "model_used",
            "created_at",
        )


class ContentBriefSerializer(serializers.ModelSerializer):
    trend_title = serializers.CharField(source="trend.title", read_only=True)
    trend_slug = serializers.CharField(source="trend.slug", read_only=True)
    generated_content = GeneratedContentSerializer(many=True, read_only=True)

    class Meta:
        model = ContentBrief
        fields = (
            "id",
            "trend",
            "trend_title",
            "trend_slug",
            "business_angle",
            "founder_angle",
            "educational_angle",
            "marketing_angle",
            "talking_points",
            "perspective",
            "content_angle",
            "model_used",
            "created_at",
            "generated_content",
        )
        # trend_title/trend_slug/generated_content are already read-only
        # by virtue of being explicitly declared above; listing them
        # here too would raise DRF's "field already declared" assertion.
        # perspective/content_angle are set once at creation time (via
        # GenerateBriefRequestSerializer below), never patched directly.
        read_only_fields = (
            "id",
            "trend",
            "business_angle",
            "founder_angle",
            "educational_angle",
            "marketing_angle",
            "talking_points",
            "perspective",
            "content_angle",
            "model_used",
            "created_at",
        )


class GenerateBriefRequestSerializer(serializers.Serializer):
    trend_slug = serializers.SlugField()
    # CONTENT PERSPECTIVE: optional — the view/service falls back to the
    # trend's best_audience when omitted, but the user can always pick
    # any of the three regardless of which one is the best audience.
    perspective = serializers.ChoiceField(
        choices=AudienceType.choices, required=False, allow_blank=True, default=""
    )


class GenerateContentRequestSerializer(serializers.Serializer):
    brief_id = serializers.UUIDField()
    content_type = serializers.ChoiceField(choices=ContentType.choices)
