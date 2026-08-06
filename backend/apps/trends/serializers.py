from rest_framework import serializers

from apps.trends.models import Category, Trend, TrendSourceLink


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug")


class TrendSourceLinkSerializer(serializers.ModelSerializer):
    platform = serializers.CharField(source="platform.name")
    platform_slug = serializers.CharField(source="platform.slug")

    class Meta:
        model = TrendSourceLink
        fields = ("platform", "platform_slug", "source_url", "created_at")


class TrendListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    platforms = serializers.SerializerMethodField()

    class Meta:
        model = Trend
        fields = (
            "id",
            "title",
            "slug",
            "category",
            "summary",
            "status",
            "estimated_lifespan",
            "first_detected_at",
            "last_seen_at",
            "platforms",
        )

    def get_platforms(self, obj) -> list[str]:
        # Relies on the view prefetching source_links__platform — avoids
        # an extra query per row when listing many trends.
        return sorted({link.platform.slug for link in obj.source_links.all()})


class TrendDetailSerializer(TrendListSerializer):
    source_links = TrendSourceLinkSerializer(many=True, read_only=True)

    class Meta(TrendListSerializer.Meta):
        fields = TrendListSerializer.Meta.fields + ("why_spreading", "source_links", "created_at")
