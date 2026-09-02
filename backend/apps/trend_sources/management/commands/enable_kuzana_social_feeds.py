from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.trend_sources.models import Platform


YOUTUBE_SLUGS = (
    "youtube-shorts-kenyan-business",
    "youtube-shorts-african-startups",
)
X_SLUGS = ("x-kenyan-founders-smes", "x-african-funding-business")


class Command(BaseCommand):
    help = (
        "Enables the seeded Kuzana YouTube Shorts and X feeds after their official "
        "API credentials are configured."
    )

    def handle(self, *args, **options):
        missing = []
        if not settings.YOUTUBE_API_KEY:
            missing.append("YOUTUBE_API_KEY")
        if not settings.X_BEARER_TOKEN:
            missing.append("X_BEARER_TOKEN")
        if missing:
            raise CommandError(
                "Kuzana social feeds remain disabled. Configure "
                + ", ".join(missing)
                + " in backend/.env first."
            )

        expected = (*YOUTUBE_SLUGS, *X_SLUGS)
        present = set(Platform.objects.filter(slug__in=expected).values_list("slug", flat=True))
        absent = set(expected) - present
        if absent:
            raise CommandError(
                "Missing seeded feeds: "
                + ", ".join(sorted(absent))
                + ". Run `manage.py seed_platforms` first."
            )

        updated = Platform.objects.filter(slug__in=expected, is_active=False).update(
            is_active=True
        )
        self.stdout.write(self.style.SUCCESS(f"Enabled {updated} Kuzana social feed(s)."))
