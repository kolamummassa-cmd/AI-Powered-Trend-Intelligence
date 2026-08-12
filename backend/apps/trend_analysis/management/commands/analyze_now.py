from django.core.management.base import BaseCommand

from apps.trend_analysis.tasks import analyze_trend_task
from apps.trends.models import Trend


class Command(BaseCommand):
    help = (
        "Analyzes every trend that hasn't been analyzed yet (analyzed_at is null). "
        "Handy in local dev to backfill trends that were ingested before AI keys "
        "were configured, without waiting for the automatic trigger."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Re-analyze every trend, including ones already analyzed.",
        )
        parser.add_argument("--slug", help="Only analyze the trend with this slug.")

    def handle(self, *args, **options):
        queryset = Trend.objects.all()
        if options["slug"]:
            queryset = queryset.filter(slug=options["slug"])
        elif not options["all"]:
            queryset = queryset.filter(analyzed_at__isnull=True)

        if not queryset.exists():
            self.stdout.write(self.style.WARNING("Nothing to analyze."))
            return

        for trend in queryset:
            self.stdout.write(f"Analyzing: {trend.title}...")
            try:
                result = analyze_trend_task(str(trend.id))
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  trend_score={result.get('trend_score')} "
                        f"opportunity_score={result.get('opportunity_score')}"
                    )
                )
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"  failed: {exc}"))

        self.stdout.write(self.style.SUCCESS("Done."))
