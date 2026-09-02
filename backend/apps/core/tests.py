import uuid

import pytest
from django.db import models
from rest_framework.test import APIClient

from apps.core.models import BaseModel


# A throwaway concrete model purely so BaseModel's soft-delete behaviour
# has something to operate on in a unit test. It is never migrated —
# the tests below stub out .save() so no database table is required.
class _SoftDeleteSample(BaseModel):
    name = models.CharField(max_length=50)

    class Meta:
        app_label = "core"
        managed = False


@pytest.mark.django_db
class TestHealthCheck:
    def test_health_check_returns_ok_when_db_is_reachable(self):
        client = APIClient()
        response = client.get("/api/v1/health/")
        assert response.status_code == 200
        assert response.data["status"] == "ok"
        assert response.data["database"] == "ok"

    def test_health_check_does_not_require_authentication(self):
        client = APIClient()
        response = client.get("/api/v1/health/")
        assert response.status_code != 401


class TestBaseModelSoftDelete:
    """Exercises the mixin logic directly, without a database, by
    stubbing save(). Keeps this test fast and independent of whatever
    real models end up inheriting BaseModel in later phases.
    """

    def test_delete_sets_deleted_at_instead_of_removing_row(self, monkeypatch):
        saved = {}

        def fake_save(self, update_fields=None):
            saved["update_fields"] = update_fields

        monkeypatch.setattr(_SoftDeleteSample, "save", fake_save)

        obj = _SoftDeleteSample(id=uuid.uuid4(), name="sample")
        assert obj.is_deleted is False

        obj.delete()

        assert obj.deleted_at is not None
        assert obj.is_deleted is True
        assert saved["update_fields"] == ["deleted_at"]

    def test_restore_clears_deleted_at(self, monkeypatch):
        monkeypatch.setattr(_SoftDeleteSample, "save", lambda self, update_fields=None: None)

        obj = _SoftDeleteSample(id=uuid.uuid4(), name="sample")
        obj.delete()
        obj.restore()

        assert obj.deleted_at is None
        assert obj.is_deleted is False

    def test_hard_delete_calls_the_real_queryset_delete(self, monkeypatch):
        called = {}

        def fake_super_delete(self, using=None, keep_parents=False):
            called["hit"] = True
            return 1, {}

        monkeypatch.setattr(models.Model, "delete", fake_super_delete)

        obj = _SoftDeleteSample(id=uuid.uuid4(), name="sample")
        obj.delete(hard=True)

        assert called.get("hit") is True
