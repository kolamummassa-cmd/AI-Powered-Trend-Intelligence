from django.core.management.base import BaseCommand

from apps.trend_sources.models import Platform

# Starter set for Phase 2 — official/low-friction sources first, per
# the roadmap. Add rows here (or via /admin/) for more RSS feeds
# without touching any code.
DEFAULT_PLATFORMS = [
    {
        "name": "Google Trends (Kenya)",
        "slug": "google-trends-ke",
        "adapter_key": "google-trends",
        "config": {"geo": "KE"},
        "poll_interval_minutes": 60,
    },
    {
        "name": "Reddit: r/startups",
        "slug": "reddit-startups",
        "adapter_key": "reddit",
        "config": {"subreddit": "startups", "limit": 25},
        "poll_interval_minutes": 30,
    },
    {
        "name": "Reddit: r/Entrepreneur",
        "slug": "reddit-entrepreneur",
        "adapter_key": "reddit",
        "config": {"subreddit": "Entrepreneur", "limit": 25},
        "poll_interval_minutes": 30,
    },
    {
        # A placeholder RSS source to prove the pipeline end-to-end.
        # Business Daily Africa's feed was tried here first but returns
        # malformed XML feedparser can't extract entries from — swap in
        # whichever Kenyan news feed you've confirmed actually parses
        # (check with `feedparser.parse(url).entries` in a shell first),
        # or add it as a second Platform row via /admin/ without
        # removing this one.
        "name": "TechCrunch (RSS)",
        "slug": "techcrunch-rss",
        "adapter_key": "rss",
        "config": {"feed_url": "https://techcrunch.com/feed/"},
        "poll_interval_minutes": 60,
    },
]


class Command(BaseCommand):
    help = "Creates the starter set of trend-monitoring Platform rows if they don't already exist."

    def handle(self, *args, **options):
        created_count = 0
        for entry in DEFAULT_PLATFORMS:
            _, created = Platform.objects.get_or_create(slug=entry["slug"], defaults=entry)
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created platform: {entry['name']}"))
            else:
                self.stdout.write(f"Already exists: {entry['name']}")

        self.stdout.write(self.style.SUCCESS(f"Done — {created_count} new platform(s) created."))
