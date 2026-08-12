from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from ai_providers.base import ContentBriefResult, ContentPieceResult
from apps.accounts.models import User
from apps.content_studio.models import ContentBrief, GeneratedContent
from apps.content_studio.services import generate_brief, generate_content
from apps.trend_sources.models import Platform
from apps.trends.models import Trend

FAKE_BRIEF_RESULT = ContentBriefResult(
    business_angle="Business angle.",
    founder_angle="Founder angle.",
    educational_angle="Educational angle.",
    marketing_angle="Marketing angle.",
    talking_points=["Point one", "Point two"],
    content_angle="A perspective-driven angle.",
)

FAKE_CONTENT_RESULT = ContentPieceResult(body="Generated content body.")


@pytest.fixture
def trend(db):
    Platform.objects.create(name="Test Platform", slug="test-platform", adapter_key="rss")
    now = timezone.now()
    return Trend.objects.create(
        title="Kenya's Fintech Boom",
        dedup_key="kenyas fintech boom",
        first_detected_at=now,
        last_seen_at=now,
    )


@pytest.fixture
def brief(db, trend):
    return ContentBrief.objects.create(
        trend=trend,
        business_angle="Business angle.",
        founder_angle="Founder angle.",
        educational_angle="Educational angle.",
        marketing_angle="Marketing angle.",
        talking_points=["Point one", "Point two"],
    )


@pytest.fixture
def user(db):
    return User.objects.create_user(email="creator@example.com", password="a-strong-passw0rd1")


def _authed_client(user):
    token = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


@pytest.mark.django_db
class TestGenerateBrief:
    @patch("apps.content_studio.services.get_ai_provider")
    def test_creates_a_brief(self, mock_get_provider, trend, user):
        mock_provider = MagicMock()
        mock_provider.generate_content_brief.return_value = FAKE_BRIEF_RESULT
        mock_get_provider.return_value = mock_provider

        result = generate_brief(trend, user=user)

        assert isinstance(result, ContentBrief)
        assert result.business_angle == "Business angle."
        assert result.created_by == user
        assert result.talking_points == ["Point one", "Point two"]

    @patch("apps.content_studio.services.get_ai_provider")
    def test_repeated_calls_create_separate_briefs(self, mock_get_provider, trend):
        mock_provider = MagicMock()
        mock_provider.generate_content_brief.return_value = FAKE_BRIEF_RESULT
        mock_get_provider.return_value = mock_provider

        generate_brief(trend)
        generate_brief(trend)

        assert ContentBrief.objects.filter(trend=trend).count() == 2

    @patch("apps.content_studio.services.get_ai_provider")
    def test_anonymous_user_leaves_created_by_null(self, mock_get_provider, trend):
        mock_provider = MagicMock()
        mock_provider.generate_content_brief.return_value = FAKE_BRIEF_RESULT
        mock_get_provider.return_value = mock_provider

        result = generate_brief(trend, user=None)

        assert result.created_by is None

    @patch("apps.content_studio.services.get_ai_provider")
    def test_explicit_perspective_is_persisted_and_sent_to_the_provider(
        self, mock_get_provider, trend
    ):
        mock_provider = MagicMock()
        mock_provider.generate_content_brief.return_value = FAKE_BRIEF_RESULT
        mock_get_provider.return_value = mock_provider

        result = generate_brief(trend, perspective="investors")

        assert result.perspective == "investors"
        assert result.content_angle == "A perspective-driven angle."
        sent_context = mock_provider.generate_content_brief.call_args[0][0]
        assert sent_context.perspective == "investors"

    @patch("apps.content_studio.services.get_ai_provider")
    def test_defaults_to_trend_best_audience_when_perspective_omitted(
        self, mock_get_provider, trend
    ):
        trend.best_audience = "founders"
        trend.save(update_fields=["best_audience"])
        mock_provider = MagicMock()
        mock_provider.generate_content_brief.return_value = FAKE_BRIEF_RESULT
        mock_get_provider.return_value = mock_provider

        result = generate_brief(trend)

        assert result.perspective == "founders"

    @patch("apps.content_studio.services.get_ai_provider")
    def test_user_can_choose_a_perspective_other_than_best_audience(self, mock_get_provider, trend):
        trend.best_audience = "founders"
        trend.save(update_fields=["best_audience"])
        mock_provider = MagicMock()
        mock_provider.generate_content_brief.return_value = FAKE_BRIEF_RESULT
        mock_get_provider.return_value = mock_provider

        result = generate_brief(trend, perspective="investors")

        assert result.perspective == "investors"
        assert trend.best_audience == "founders"


@pytest.mark.django_db
class TestGenerateContent:
    @patch("apps.content_studio.services.get_ai_provider")
    def test_creates_content_with_version_one(self, mock_get_provider, brief, user):
        mock_provider = MagicMock()
        mock_provider.generate_content_piece.return_value = FAKE_CONTENT_RESULT
        mock_get_provider.return_value = mock_provider

        content = generate_content(brief, "hook", user=user)

        assert isinstance(content, GeneratedContent)
        assert content.body == "Generated content body."
        assert content.version == 1
        assert content.created_by == user
        assert content.is_saved is False

    @patch("apps.content_studio.services.get_ai_provider")
    def test_regenerating_increments_version(self, mock_get_provider, brief):
        mock_provider = MagicMock()
        mock_provider.generate_content_piece.return_value = FAKE_CONTENT_RESULT
        mock_get_provider.return_value = mock_provider

        first = generate_content(brief, "hook")
        second = generate_content(brief, "hook")

        assert first.version == 1
        assert second.version == 2
        assert GeneratedContent.objects.filter(brief=brief, content_type="hook").count() == 2

    @patch("apps.content_studio.services.get_ai_provider")
    def test_different_content_types_version_independently(self, mock_get_provider, brief):
        mock_provider = MagicMock()
        mock_provider.generate_content_piece.return_value = FAKE_CONTENT_RESULT
        mock_get_provider.return_value = mock_provider

        hook = generate_content(brief, "hook")
        cta = generate_content(brief, "cta")

        assert hook.version == 1
        assert cta.version == 1

    @patch("apps.content_studio.services.get_ai_provider")
    def test_passes_the_mapped_angle_to_the_provider(self, mock_get_provider, brief):
        # `brief` fixture has no content_angle set (perspective wasn't
        # used to create it), so this exercises the original fallback
        # mapping — unchanged behavior for briefs predating perspective.
        mock_provider = MagicMock()
        mock_provider.generate_content_piece.return_value = FAKE_CONTENT_RESULT
        mock_get_provider.return_value = mock_provider

        generate_content(brief, "cta")

        call_context = mock_provider.generate_content_piece.call_args[0][0]
        assert call_context.angle == brief.marketing_angle
        assert call_context.content_type == "cta"

    @patch("apps.content_studio.services.get_ai_provider")
    def test_content_angle_takes_priority_when_present(self, mock_get_provider, trend):
        perspective_brief = ContentBrief.objects.create(
            trend=trend,
            business_angle="Business angle.",
            marketing_angle="Marketing angle.",
            perspective="investors",
            content_angle="An investor-focused angle.",
        )
        mock_provider = MagicMock()
        mock_provider.generate_content_piece.return_value = FAKE_CONTENT_RESULT
        mock_get_provider.return_value = mock_provider

        generate_content(perspective_brief, "cta")

        call_context = mock_provider.generate_content_piece.call_args[0][0]
        assert call_context.angle == "An investor-focused angle."
        assert call_context.perspective == "investors"

    @patch("apps.content_studio.services.get_ai_provider")
    def test_same_trend_different_perspectives_send_different_context(
        self, mock_get_provider, trend
    ):
        """The whole point of Content Perspective: the same trend must
        produce a meaningfully different generation context for
        Founders vs. Investors."""
        founders_brief = ContentBrief.objects.create(
            trend=trend, perspective="founders", content_angle="A founder-focused angle."
        )
        investors_brief = ContentBrief.objects.create(
            trend=trend, perspective="investors", content_angle="An investor-focused angle."
        )
        mock_provider = MagicMock()
        mock_provider.generate_content_piece.return_value = FAKE_CONTENT_RESULT
        mock_get_provider.return_value = mock_provider

        generate_content(founders_brief, "hook")
        founders_context = mock_provider.generate_content_piece.call_args[0][0]

        generate_content(investors_brief, "hook")
        investors_context = mock_provider.generate_content_piece.call_args[0][0]

        assert founders_context.perspective != investors_context.perspective
        assert founders_context.angle != investors_context.angle


@pytest.mark.django_db
class TestGenerateBriefTask:
    @patch("apps.content_studio.tasks.generate_brief")
    def test_returns_brief_id_on_success(self, mock_generate, trend):
        from apps.content_studio.tasks import generate_brief_task

        mock_generate.return_value = MagicMock(id="fake-brief-id", trend=trend)
        result = generate_brief_task(str(trend.id))

        assert result["trend"] == str(trend.id)

    def test_missing_trend_returns_error_without_raising(self):
        from apps.content_studio.tasks import generate_brief_task
        import uuid

        result = generate_brief_task(str(uuid.uuid4()))
        assert result["error"] == "not found"

    @patch("apps.content_studio.tasks.generate_brief")
    def test_notifies_the_triggering_user(self, mock_generate, trend, user):
        from apps.content_studio.tasks import generate_brief_task
        from apps.notifications.models import Notification, NotificationType

        mock_generate.return_value = MagicMock(id="fake-brief-id", trend=trend)
        generate_brief_task(str(trend.id), user_id=str(user.id))

        assert Notification.objects.filter(
            user=user, type=NotificationType.GENERATION_COMPLETE
        ).exists()

    @patch("apps.content_studio.tasks.generate_brief")
    def test_no_notification_without_a_user(self, mock_generate, trend):
        from apps.content_studio.tasks import generate_brief_task
        from apps.notifications.models import Notification

        mock_generate.return_value = MagicMock(id="fake-brief-id", trend=trend)
        generate_brief_task(str(trend.id))

        assert not Notification.objects.exists()


@pytest.mark.django_db
class TestGenerateContentTask:
    @patch("apps.content_studio.tasks.generate_content")
    def test_returns_content_type_on_success(self, mock_generate, brief):
        from apps.content_studio.tasks import generate_content_task

        mock_generate.return_value = MagicMock(id="fake-id", content_type="hook")
        result = generate_content_task(str(brief.id), "hook")

        assert result["content_type"] == "hook"

    def test_missing_brief_returns_error_without_raising(self):
        from apps.content_studio.tasks import generate_content_task
        import uuid

        result = generate_content_task(str(uuid.uuid4()), "hook")
        assert result["error"] == "not found"

    @patch("apps.content_studio.tasks.generate_content")
    def test_notifies_the_triggering_user(self, mock_generate, brief, user):
        from apps.content_studio.tasks import generate_content_task
        from apps.notifications.models import Notification, NotificationType

        mock_generate.return_value = MagicMock(id="fake-id", content_type="hook")
        generate_content_task(str(brief.id), "hook", user_id=str(user.id))

        assert Notification.objects.filter(
            user=user, type=NotificationType.GENERATION_COMPLETE
        ).exists()


@pytest.mark.django_db
class TestContentBriefAPI:
    def test_list_requires_authentication(self):
        client = APIClient()
        response = client.get("/api/v1/content/briefs/")
        assert response.status_code == 401

    def test_list_filters_by_trend_slug(self, brief, user, trend):
        other_trend = Trend.objects.create(
            title="Other Trend",
            dedup_key="other trend",
            first_detected_at=timezone.now(),
            last_seen_at=timezone.now(),
        )
        ContentBrief.objects.create(trend=other_trend)

        client = _authed_client(user)
        response = client.get("/api/v1/content/briefs/", {"trend": trend.slug})

        assert response.data["count"] == 1
        assert response.data["results"][0]["trend_slug"] == trend.slug

    @patch("apps.content_studio.views.generate_brief")
    def test_create_generates_a_brief(self, mock_generate, trend, user):
        mock_generate.return_value = ContentBrief.objects.create(
            trend=trend,
            business_angle="x",
            founder_angle="y",
            educational_angle="z",
            marketing_angle="w",
            talking_points=["a"],
        )

        client = _authed_client(user)
        response = client.post("/api/v1/content/briefs/", {"trend_slug": trend.slug})

        assert response.status_code == 201
        assert response.data["trend_slug"] == trend.slug
        mock_generate.assert_called_once()

    @patch("apps.content_studio.views.generate_brief")
    def test_create_passes_perspective_through_to_the_service(self, mock_generate, trend, user):
        mock_generate.return_value = ContentBrief.objects.create(
            trend=trend, perspective="investors", content_angle="x"
        )

        client = _authed_client(user)
        client.post(
            "/api/v1/content/briefs/",
            {"trend_slug": trend.slug, "perspective": "investors"},
            format="json",
        )

        mock_generate.assert_called_once_with(trend, user=user, perspective="investors")

    @patch("apps.content_studio.views.generate_brief")
    def test_create_returns_502_on_provider_error(self, mock_generate, trend, user):
        from ai_providers.base import AIProviderError

        mock_generate.side_effect = AIProviderError("boom")

        client = _authed_client(user)
        response = client.post("/api/v1/content/briefs/", {"trend_slug": trend.slug})

        assert response.status_code == 502

    def test_detail_includes_generated_content(self, brief, user):
        GeneratedContent.objects.create(brief=brief, content_type="hook", body="A hook", version=1)

        client = _authed_client(user)
        response = client.get(f"/api/v1/content/briefs/{brief.id}/")

        assert response.status_code == 200
        assert len(response.data["generated_content"]) == 1


@pytest.mark.django_db
class TestGeneratedContentAPI:
    @patch("apps.content_studio.views.generate_content")
    def test_create_generates_content(self, mock_generate, brief, user):
        mock_generate.return_value = GeneratedContent.objects.create(
            brief=brief, content_type="hook", body="A hook", version=1
        )

        client = _authed_client(user)
        response = client.post(
            "/api/v1/content/pieces/", {"brief_id": str(brief.id), "content_type": "hook"}
        )

        assert response.status_code == 201
        assert response.data["content_type"] == "hook"

    def test_filters_by_brief_and_is_saved(self, brief, user):
        saved = GeneratedContent.objects.create(
            brief=brief, content_type="hook", body="saved", version=1, is_saved=True
        )
        GeneratedContent.objects.create(
            brief=brief, content_type="cta", body="unsaved", version=1, is_saved=False
        )

        client = _authed_client(user)
        response = client.get(
            "/api/v1/content/pieces/", {"brief": str(brief.id), "is_saved": "true"}
        )

        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == str(saved.id)

    def test_patch_toggles_is_saved(self, brief, user):
        content = GeneratedContent.objects.create(
            brief=brief, content_type="hook", body="A hook", version=1
        )

        client = _authed_client(user)
        response = client.patch(f"/api/v1/content/pieces/{content.id}/", {"is_saved": True})

        assert response.status_code == 200
        content.refresh_from_db()
        assert content.is_saved is True

    def test_patch_unsaving_via_multipart_works(self, brief, user):
        """Regression coverage: PATCH {"is_saved": False} without an
        explicit format used to be misread by an earlier version of this
        view's usage-event logic (multipart encodes False as the truthy
        string "False"). That event logic is gone now, but the underlying
        multipart unsave behavior itself is still worth pinning down.
        """
        content = GeneratedContent.objects.create(
            brief=brief, content_type="hook", body="A hook", version=1, is_saved=True
        )

        client = _authed_client(user)
        client.patch(f"/api/v1/content/pieces/{content.id}/", {"is_saved": False})

        content.refresh_from_db()
        assert content.is_saved is False

    def test_patch_cannot_change_body(self, brief, user):
        content = GeneratedContent.objects.create(
            brief=brief, content_type="hook", body="Original", version=1
        )

        client = _authed_client(user)
        client.patch(f"/api/v1/content/pieces/{content.id}/", {"body": "Hacked"})

        content.refresh_from_db()
        assert content.body == "Original"
