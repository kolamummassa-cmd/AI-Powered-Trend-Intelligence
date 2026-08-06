from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.trend_sources.models import Platform
from apps.trend_sources.tasks import poll_platform


class Command(BaseCommand):
    help = (
        "Polls every active platform immediately, ignoring poll_interval_minutes. "
        "Handy in local dev (with CELERY_TASK_ALWAYS_EAGER=True) to populate the "
        "trend feed without waiting for Celery Beat's schedule."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--platform",
            help="Only poll the platform with this slug (default: all active platforms).",
        )

    def handle(self, *args, **options):
        queryset = Platform.objects.filter(is_active=True)
        if options["platform"]:
            queryset = queryset.filter(slug=options["platform"])

        if not queryset.exists():
            self.stdout.write(self.style.WARNING("No matching active platforms found."))
            return

        for platform in queryset:
            self.stdout.write(f"Polling {platform.name} ({platform.slug})...")
            try:
                result = poll_platform(str(platform.id))
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  fetched={result.get('fetched')} new={result.get('new')}"
                    )
                )
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"  failed: {exc}"))

        self.stdout.write(self.style.SUCCESS(f"Done at {timezone.now().isoformat()}."))
