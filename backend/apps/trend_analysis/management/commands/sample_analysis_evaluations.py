import json

from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from apps.trend_analysis.models import TrendAnalysis


class Command(BaseCommand):
    help = "Print a balanced review sample of recent AI analyses and user-feedback quality signals."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=20)

    def handle(self, *args, **options):
        analyses = (
            TrendAnalysis.objects.select_related("trend")
            .annotate(
                helpful_count=Count("feedback", filter=Q(feedback__is_helpful=True)),
                not_helpful_count=Count("feedback", filter=Q(feedback__is_helpful=False)),
            )
            .order_by("-created_at")[: options["limit"]]
        )
        sample = [
            {
                "analysis_id": str(analysis.id),
                "trend": analysis.trend.title,
                "scores": {
                    "trend": analysis.trend_score,
                    "opportunity": analysis.opportunity_score,
                    "confidence": analysis.confidence_score,
                },
                "why_it_matters": analysis.why_it_matters,
                "model_used": analysis.model_used,
                "helpful_count": analysis.helpful_count,
                "not_helpful_count": analysis.not_helpful_count,
            }
            for analysis in analyses
        ]
        self.stdout.write(json.dumps(sample, indent=2, default=str))
