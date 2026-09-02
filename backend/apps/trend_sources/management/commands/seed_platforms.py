from django.core.management.base import BaseCommand

from apps.trend_sources.models import Platform

# RSS is active by default. Kuzana-focused X and YouTube Shorts feeds are
# also seeded below, but deliberately disabled until an operator supplies the
# required official API credentials and explicitly enables them. This avoids a
# local development startup endlessly retrying an unauthenticated source.
#
# poll_interval_minutes=20 matches the current RSS polling requirement.
# Add more verified RSS feeds here (or via /admin/) without touching
# any other code — confirm a candidate feed actually parses first with
# `feedparser.parse(url).entries` in a shell before adding it.
#
# IMPORTANT: the feed URLs below beyond TechCrunch's main feed were
# never reachable from the sandbox this codebase was developed in (no
# outbound network access), so they're added on the strength of being
# well-known, publicly documented RSS endpoints for each publication —
# not independently verified with `feedparser.parse(url).entries`.
# After the first real deploy, check Django Admin → Trend sources →
# Platforms: any row with a growing "failures" count or a stale
# last_polled_at is worth disabling or fixing (one bad feed can't take
# down the others — poll_platform runs per-platform with its own
# retry). Business Daily Africa was tried here previously and
# confirmed to return malformed XML feedparser can't parse — left out
# entirely rather than seeded broken.
DEFAULT_PLATFORMS = [
    {
        "name": "TechCrunch",
        "slug": "techcrunch-rss",
        "adapter_key": "rss",
        "config": {"feed_url": "https://techcrunch.com/feed/"},
        "poll_interval_minutes": 20,
        "credibility_weight": 80,
        "kuzana_priority_weight": 40,
        "is_active": True,
    },
    {
        "name": "TechCrunch: Startups",
        "slug": "techcrunch-startups-rss",
        "adapter_key": "rss",
        "config": {"feed_url": "https://techcrunch.com/category/startups/feed/"},
        "poll_interval_minutes": 20,
        "credibility_weight": 80,
        "kuzana_priority_weight": 45,
        "is_active": True,
    },
    {
        "name": "TechCrunch: Venture",
        "slug": "techcrunch-venture-rss",
        "adapter_key": "rss",
        "config": {"feed_url": "https://techcrunch.com/category/venture/feed/"},
        "poll_interval_minutes": 20,
        "credibility_weight": 80,
        "kuzana_priority_weight": 45,
        "is_active": True,
    },
    {
        "name": "VentureBeat: AI",
        "slug": "venturebeat-ai-rss",
        "adapter_key": "rss",
        "config": {"feed_url": "https://venturebeat.com/category/ai/feed/"},
        "poll_interval_minutes": 20,
        "credibility_weight": 75,
        "kuzana_priority_weight": 40,
        "is_active": True,
    },
    {
        "name": "MIT Technology Review",
        "slug": "mit-tech-review-rss",
        "adapter_key": "rss",
        "config": {"feed_url": "https://www.technologyreview.com/feed/"},
        "poll_interval_minutes": 20,
        "credibility_weight": 85,
        "kuzana_priority_weight": 35,
        "is_active": True,
    },
    {
        "name": "Hacker News: Front Page",
        "slug": "hacker-news-frontpage-rss",
        "adapter_key": "rss",
        "config": {"feed_url": "https://hnrss.org/frontpage"},
        "poll_interval_minutes": 20,
        "credibility_weight": 55,
        "kuzana_priority_weight": 35,
        "is_active": True,
    },
    # African/Kenyan tech + business coverage — the niche-relevance
    # focus the product is built around, not just global tech news.
    {
        "name": "TechCabal",
        "slug": "techcabal-rss",
        "adapter_key": "rss",
        "config": {"feed_url": "https://techcabal.com/feed/"},
        "poll_interval_minutes": 20,
        "credibility_weight": 75,
        "kuzana_priority_weight": 90,
        "is_active": True,
    },
    {
        "name": "Disrupt Africa",
        "slug": "disrupt-africa-rss",
        "adapter_key": "rss",
        "config": {"feed_url": "https://disrupt-africa.com/feed/"},
        "poll_interval_minutes": 20,
        "credibility_weight": 70,
        "kuzana_priority_weight": 85,
        "is_active": True,
    },
    {
        "name": "Rest of World",
        "slug": "rest-of-world-rss",
        "adapter_key": "rss",
        "config": {"feed_url": "https://restofworld.org/feed/"},
        "poll_interval_minutes": 20,
        "credibility_weight": 75,
        "kuzana_priority_weight": 60,
        "is_active": True,
    },
    {
        "name": "African Business",
        "slug": "african-business-rss",
        "adapter_key": "rss",
        "config": {"feed_url": "https://african.business/feed/"},
        "poll_interval_minutes": 20,
        "credibility_weight": 70,
        "kuzana_priority_weight": 80,
        "is_active": True,
    },
    # Kuzana social feeds. These are deliberately narrow searches: YouTube
    # and X do not expose a reliable general "what is trending in Kenya"
    # firehose to ordinary API accounts, so focused business/founder queries
    # produce a more useful and explainable signal set.
    {
        "name": "YouTube Shorts: Kenyan business",
        "slug": "youtube-shorts-kenyan-business",
        "adapter_key": "youtube-shorts",
        "config": {
            "query": "Kenya business entrepreneurship",
            "region_code": "KE",
            "max_results": 25,
        },
        "poll_interval_minutes": 30,
        "credibility_weight": 55,
        "kuzana_priority_weight": 85,
        "is_active": False,
    },
    {
        "name": "YouTube Shorts: African startups",
        "slug": "youtube-shorts-african-startups",
        "adapter_key": "youtube-shorts",
        "config": {
            "query": "African startups founders fintech",
            "region_code": "KE",
            "max_results": 25,
        },
        "poll_interval_minutes": 30,
        "credibility_weight": 55,
        "kuzana_priority_weight": 75,
        "is_active": False,
    },
    {
        "name": "X: Kenyan founders and SMEs",
        "slug": "x-kenyan-founders-smes",
        "adapter_key": "x",
        "config": {
            "query": (
                "(Kenya OR Kenyan) (startup OR founder OR entrepreneur OR SME OR fintech) "
                "-is:retweet lang:en"
            ),
            "max_results": 50,
        },
        "poll_interval_minutes": 15,
        "credibility_weight": 45,
        "kuzana_priority_weight": 85,
        "is_active": False,
    },
    {
        "name": "X: African funding and business",
        "slug": "x-african-funding-business",
        "adapter_key": "x",
        "config": {
            "query": (
                "(Africa OR Kenyan) (funding OR raised OR investment OR business) "
                "-is:retweet lang:en"
            ),
            "max_results": 50,
        },
        "poll_interval_minutes": 15,
        "credibility_weight": 45,
        "kuzana_priority_weight": 75,
        "is_active": False,
    },
]

# Slugs to deactivate if they already exist in the database — either
# legacy non-RSS platforms from before RSS became the sole active
# source, or RSS feeds confirmed (by actually running this) to return
# malformed XML feedparser can't parse. Deactivated rather than
# deleted — preserves any signals/trends already collected from them,
# and an operator can always re-enable one from /admin/ if that
# decision changes (e.g. the publication fixes their feed).
DEACTIVATE_SLUGS = [
    "google-trends-ke",
    "reddit-startups",
    "reddit-entrepreneur",
    # Confirmed 2026-08-11: malformed XML ("mismatched tag") — same
    # failure mode Business Daily Africa had, which is why that one was
    # never added to DEFAULT_PLATFORMS at all.
    "techpoint-africa-rss",
]


class Command(BaseCommand):
    help = (
        "Creates starter RSS and disabled Kuzana social Platform rows if they don't already exist, "
        "and deactivates legacy generic social platforms from earlier phases. "
        "Idempotent — safe to run on every deploy."
    )

    def handle(self, *args, **options):
        created_count = 0
        for entry in DEFAULT_PLATFORMS:
            platform, created = Platform.objects.get_or_create(slug=entry["slug"], defaults=entry)
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created platform: {entry['name']}"))
            else:
                # These are product-owned source rankings, not user-entered
                # feeds. Keep the priority policy current on every seed while
                # leaving activation state and query configuration untouched.
                Platform.objects.filter(id=platform.id).update(
                    credibility_weight=entry["credibility_weight"],
                    kuzana_priority_weight=entry["kuzana_priority_weight"],
                )
                self.stdout.write(f"Already exists: {entry['name']}")

        deactivated = Platform.objects.filter(slug__in=DEACTIVATE_SLUGS, is_active=True).update(
            is_active=False
        )
        if deactivated:
            self.stdout.write(
                self.style.WARNING(
                    f"Deactivated {deactivated} legacy/broken platform(s) — "
                    "see DEACTIVATE_SLUGS for why."
                )
            )

        self.stdout.write(self.style.SUCCESS(f"Done — {created_count} new platform(s) created."))
