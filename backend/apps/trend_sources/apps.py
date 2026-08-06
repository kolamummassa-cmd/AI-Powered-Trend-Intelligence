from django.apps import AppConfig


class TrendSourcesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.trend_sources"
    label = "trend_sources"
    verbose_name = "Trend Sources"

    def ready(self):
        # Importing this module is what populates the adapter registry
        # (each adapter self-registers via @register_adapter at import
        # time) — without this, `ready()` would never trigger the import
        # and the registry would be empty at request time.
        from apps.trend_sources import adapters  # noqa: F401
