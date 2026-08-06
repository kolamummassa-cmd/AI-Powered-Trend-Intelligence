import django_filters

from apps.trends.models import Trend, TrendStatus


class TrendFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category__slug", lookup_expr="iexact")
    platform = django_filters.CharFilter(
        field_name="source_links__platform__slug", lookup_expr="iexact", distinct=True
    )
    status = django_filters.ChoiceFilter(choices=TrendStatus.choices)
    since = django_filters.IsoDateTimeFilter(field_name="first_detected_at", lookup_expr="gte")

    class Meta:
        model = Trend
        fields = ["category", "platform", "status", "since"]
