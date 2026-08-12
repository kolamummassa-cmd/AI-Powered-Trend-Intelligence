import django_filters

from apps.trends.models import AudienceType, Trend, TrendStage, TrendStatus

# Matches the spec's "High Priority" filter — a single toggle rather
# than making the user pick their own score thresholds.
HIGH_PRIORITY_TREND_SCORE = 70
HIGH_PRIORITY_OPPORTUNITY_SCORE = 70

# A trend "is relevant" to an audience filter once its score for that
# persona clears this bar — deliberately a relevance threshold, not an
# exact match on best_audience, so a trend can show up for more than
# one audience filter (its best audience just happens to score higher).
AUDIENCE_RELEVANCE_THRESHOLD = 60

AUDIENCE_SCORE_FIELD = {
    AudienceType.CONTENT_CREATORS: "content_creator_score",
    AudienceType.FOUNDERS: "founder_score",
    AudienceType.INVESTORS: "investor_score",
}


class TrendFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category__slug", lookup_expr="iexact")
    platform = django_filters.CharFilter(
        field_name="source_links__platform__slug", lookup_expr="iexact", distinct=True
    )
    status = django_filters.ChoiceFilter(choices=TrendStatus.choices)
    stage = django_filters.ChoiceFilter(field_name="trend_stage", choices=TrendStage.choices)
    since = django_filters.IsoDateTimeFilter(field_name="first_detected_at", lookup_expr="gte")
    min_trend_score = django_filters.NumberFilter(field_name="trend_score", lookup_expr="gte")
    min_opportunity_score = django_filters.NumberFilter(
        field_name="opportunity_score", lookup_expr="gte"
    )
    high_priority = django_filters.BooleanFilter(method="filter_high_priority")
    # "All Audiences" is simply omitting this param — there's still one
    # unified trend feed, this only narrows it by stored relevance.
    audience = django_filters.ChoiceFilter(choices=AudienceType.choices, method="filter_audience")

    class Meta:
        model = Trend
        fields = [
            "category",
            "platform",
            "status",
            "stage",
            "since",
            "min_trend_score",
            "min_opportunity_score",
            "high_priority",
            "audience",
        ]

    def filter_high_priority(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            trend_score__gte=HIGH_PRIORITY_TREND_SCORE,
            opportunity_score__gte=HIGH_PRIORITY_OPPORTUNITY_SCORE,
        )

    def filter_audience(self, queryset, name, value):
        score_field = AUDIENCE_SCORE_FIELD.get(value)
        if not score_field:
            return queryset
        return queryset.filter(**{f"{score_field}__gte": AUDIENCE_RELEVANCE_THRESHOLD})
