from django.core.management.base import BaseCommand

from apps.trend_sources.tasks import poll_due_platforms


class Command(BaseCommand):
    help = (
        "Runs the same due-platform check Celery Beat normally runs every 5 "
        "minutes (see CELERY_BEAT_SCHEDULE), but immediately and synchronously. "
        "Intended to be called once from docker/start.sh on every container "
        "boot, so a fresh deploy (or a fresh database, where every Platform's "
        "last_polled_at is NULL and therefore immediately due) doesn't leave "
        "real users looking at an empty dashboard until Beat's own schedule "
        "happens to tick. Safe to run any time — it only ever queues polls "
        "for platforms that are actually due; it never forces an early poll "
        "of a platform still inside its own poll_interval_minutes window.\n\n"
        "Note this only *queues* poll_platform tasks onto Redis (via "
        "`.delay()`) — it doesn't fetch anything itself. The actual fetching "
        "happens once the Celery worker process comes up, which honcho starts "
        "moments after this command finishes, so the queued work is picked up "
        "almost immediately rather than being lost."
    )

    def handle(self, *args, **options):
        # Deliberately never raises: this runs during container boot,
        # before the app is reachable, and it's a nice-to-have (skip the
        # wait for Beat's own schedule) rather than a hard requirement —
        # if Redis isn't reachable yet for any reason, Beat's regular
        # 5-minute heartbeat still covers this once it's up. A crash
        # here should never be able to take down the whole boot sequence.
        try:
            result = poll_due_platforms()
            queued = result.get("queued", 0) if isinstance(result, dict) else 0
            self.stdout.write(self.style.SUCCESS(f"Queued {queued} due platform(s) for polling."))
        except Exception as exc:  # noqa: BLE001 — intentionally broad, see above
            self.stdout.write(
                self.style.WARNING(
                    f"Startup poll trigger failed ({exc}) — Beat's regular "
                    "5-minute heartbeat will pick this up instead."
                )
            )
