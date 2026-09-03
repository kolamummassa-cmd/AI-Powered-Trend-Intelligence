from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from ai_providers.base import ChatRefineResult
from apps.accounts.models import User
from apps.ai_chat.models import AIChatMessage
from apps.ai_chat.services import convert_for_platform, refine_content
from apps.content_studio.models import ContentBrief, GeneratedContent
from apps.core.models import AIJob
from apps.trend_sources.models import Platform
from apps.trends.models import Trend


@pytest.fixture
def content(db, user):
    Platform.objects.create(name="Test Platform", slug="test-platform", adapter_key="rss")
    now = timezone.now()
    trend = Trend.objects.create(
        title="Kenya's Fintech Boom",
        dedup_key="kenyas fintech boom",
        first_detected_at=now,
        last_seen_at=now,
    )
    brief = ContentBrief.objects.create(trend=trend, created_by=user)
    return GeneratedContent.objects.create(
        brief=brief,
        created_by=user,
        content_type="hook",
        body="Original hook body.",
        version=1,
    )


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="creator@example.com", password="a-strong-passw0rd1", is_verified=True
    )


def _authed_client(user):
    token = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


@pytest.mark.django_db
class TestRefineContent:
    @patch("apps.ai_chat.services.get_ai_provider")
    def test_creates_user_and_assistant_messages(self, mock_get_provider, content, user):
        mock_provider = MagicMock()
        mock_provider.chat_refine.return_value = ChatRefineResult(reply="Punchier hook body.")
        mock_get_provider.return_value = mock_provider

        assistant_message = refine_content(content, "Make it punchier.", user=user)

        assert assistant_message.role == "assistant"
        assert assistant_message.message == "Punchier hook body."
        messages = list(AIChatMessage.objects.filter(content=content).order_by("created_at"))
        assert [m.role for m in messages] == ["user", "assistant"]
        assert messages[0].message == "Make it punchier."

    @patch("apps.ai_chat.services.get_ai_provider")
    def test_updates_content_body_in_place(self, mock_get_provider, content):
        mock_provider = MagicMock()
        mock_provider.chat_refine.return_value = ChatRefineResult(reply="Punchier hook body.")
        mock_get_provider.return_value = mock_provider

        refine_content(content, "Make it punchier.")
        content.refresh_from_db()

        assert content.body == "Punchier hook body."
        assert content.version == 1  # refinement edits in place, doesn't bump version

    @patch("apps.ai_chat.services.get_ai_provider")
    def test_second_turn_includes_prior_history(self, mock_get_provider, content):
        mock_provider = MagicMock()
        mock_provider.chat_refine.return_value = ChatRefineResult(reply="v2")
        mock_get_provider.return_value = mock_provider
        refine_content(content, "First instruction.")

        mock_provider.chat_refine.return_value = ChatRefineResult(reply="v3")
        refine_content(content, "Second instruction.")

        call_context = mock_provider.chat_refine.call_args[0][0]
        assert len(call_context.history) == 2
        assert call_context.history[0] == ("user", "First instruction.")
        assert call_context.history[1] == ("assistant", "v2")


@pytest.mark.django_db
class TestConvertForPlatform:
    @patch("apps.ai_chat.services.get_ai_provider")
    def test_converts_using_canned_instruction(self, mock_get_provider, content):
        mock_provider = MagicMock()
        mock_provider.chat_refine.return_value = ChatRefineResult(reply="LinkedIn version.")
        mock_get_provider.return_value = mock_provider

        message = convert_for_platform(content, "linkedin")

        assert message.message == "LinkedIn version."
        call_context = mock_provider.chat_refine.call_args[0][0]
        assert "LinkedIn" in call_context.instruction

    def test_unknown_platform_raises(self, content):
        with pytest.raises(ValueError):
            convert_for_platform(content, "not-a-real-platform")


@pytest.mark.django_db
class TestAIChatAPI:
    def test_messages_require_authentication(self):
        client = APIClient()
        response = client.get("/api/v1/chat/messages/")
        assert response.status_code == 401

    def test_messages_filters_by_content(self, content, user):
        AIChatMessage.objects.create(content=content, role="user", message="Hi")
        AIChatMessage.objects.create(content=content, role="assistant", message="Hello")

        client = _authed_client(user)
        response = client.get("/api/v1/chat/messages/", {"content": str(content.id)})

        assert response.data["count"] == 2

    @patch("apps.ai_chat.views.enqueue_ai_job")
    def test_refine_endpoint_queues_job(self, mock_enqueue, content, user):

        client = _authed_client(user)
        response = client.post(
            "/api/v1/chat/refine/",
            {"content_id": str(content.id), "instruction": "Make it punchier."},
        )

        assert response.status_code == 202
        assert response.data["job_type"] == AIJob.JobType.REFINE_CONTENT


    @patch("apps.ai_chat.views.enqueue_ai_job")
    def test_convert_endpoint_queues_job(self, mock_enqueue, content, user):

        client = _authed_client(user)
        response = client.post(
            "/api/v1/chat/convert/",
            {"content_id": str(content.id), "platform": "twitter_thread"},
        )

        assert response.status_code == 202
        assert response.data["job_type"] == AIJob.JobType.CONVERT_CONTENT

    @patch("apps.ai_chat.views.enqueue_ai_job")
    def test_other_user_cannot_view_or_refine_chat(self, mock_enqueue, content):
        AIChatMessage.objects.create(content=content, role="user", message="Private")
        other = User.objects.create_user(
            email="other@example.com", password="a-strong-passw0rd1", is_verified=True
        )
        client = _authed_client(other)

        messages = client.get("/api/v1/chat/messages/", {"content": str(content.id)})
        refine = client.post(
            "/api/v1/chat/refine/",
            {"content_id": str(content.id), "instruction": "Steal this."},
        )

        assert messages.data["count"] == 0
        assert refine.status_code == 404
