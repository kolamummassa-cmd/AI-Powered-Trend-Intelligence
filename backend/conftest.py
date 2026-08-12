import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_django_cache():
    """The dashboard-stats/analytics-summary caching added in Phase 10
    uses Django's default process-wide cache backend. Test DB state
    resets between tests (transactions roll back), but that cache does
    NOT — without this, a count cached by one test would leak into the
    next test's assertions. Runs before and after every test so leakage
    can't happen in either direction.
    """
    cache.clear()
    yield
    cache.clear()
