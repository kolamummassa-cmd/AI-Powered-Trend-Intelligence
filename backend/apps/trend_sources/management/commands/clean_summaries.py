from django.core.management.base import BaseCommand

from apps.trend_sources.adapters import _clean_summary
from apps.trend_sources.models import RawTrendSignal
from apps.trends.models import Trend


class Command(BaseCommand):
    help = (
        "One-off backfill: re-applies adapters._clean_summary() (HTML-tag "
        "stripping + hnrss-style 'Article URL/Comments URL/Points/# Comments' "
        "boilerplate removal, added 2026-08-19) to every existing "
        "RawTrendSignal and Trend row. Only touches rows where the cleaned "
        "value actually differs, so it's safe to run more than once. Needed "
        "because that cleanup only applies to signals fetched *after* the "
        "fix — anything ingested before it still has the raw, untouched "
        "summary text sitting in the database."
    )

    def handle(self, *args, **options):
        signal_updates = []
        for raw_signal in RawTrendSignal.objects.exclude(summary=""):
            cleaned = _clean_summary(raw_signal.summary)
            if cleaned != raw_signal.summary:
                raw_signal.summary = cleaned
                signal_updates.append(raw_signal)
        if signal_updates:
            RawTrendSignal.objects.bulk_update(signal_updates, ["summary"])

        trend_updates = []
        for trend in Trend.objects.exclude(summary=""):
            cleaned = _clean_summary(trend.summary)
            if cleaned != trend.summary:
                trend.summary = cleaned
                trend_updates.append(trend)
        if trend_updates:
            Trend.objects.bulk_update(trend_updates, ["summary"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Cleaned {len(signal_updates)} RawTrendSignal row(s) and "
                f"{len(trend_updates)} Trend row(s)."
            )
        )
