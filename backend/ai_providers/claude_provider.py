import json
import re

from anthropic import Anthropic
from django.conf import settings

from ai_providers.base import (
    ANALYSIS_SYSTEM_PROMPT,
    CHAT_REFINE_SYSTEM_PROMPT,
    CONTENT_BRIEF_SYSTEM_PROMPT,
    AIProvider,
    AIProviderError,
    ChatRefineContext,
    ChatRefineResult,
    ContentBriefContext,
    ContentBriefResult,
    ContentPieceContext,
    ContentPieceResult,
    TrendAnalysisContext,
    TrendAnalysisResult,
    content_piece_system_prompt,
    parse_analysis_response,
    parse_content_brief_response,
)

# Same reasoning as OpenAIProvider: cheap/fast model for scoring, a
# stronger model for the Content Studio (Phase 5) where writing
# quality is what the user judges.
SCORING_MODEL = "claude-haiku-4-5-20251001"
CONTENT_MODEL = "claude-sonnet-4-5-20250929"

_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def _extract_text(response) -> str:
    return "".join(block.text for block in response.content if block.type == "text")


def _extract_json(content: str) -> dict:
    # Claude generally honours "raw JSON only", but strip any
    # accidental markdown fencing rather than failing on it.
    match = _JSON_BLOCK.search(content)
    json_text = match.group(0) if match else content
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise AIProviderError(f"Claude returned non-JSON content: {content[:200]}") from exc


class ClaudeProvider(AIProvider):
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not settings.ANTHROPIC_API_KEY:
                raise AIProviderError("ANTHROPIC_API_KEY is not configured.")
            self._client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._client

    def generate_trend_analysis(self, context: TrendAnalysisContext) -> TrendAnalysisResult:
        try:
            response = self.client.messages.create(
                model=SCORING_MODEL,
                max_tokens=1024,
                temperature=0.3,
                system=ANALYSIS_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": self._build_user_prompt(context)}],
            )
        except Exception as exc:
            raise AIProviderError(f"Claude request failed: {exc}") from exc

        return parse_analysis_response(_extract_json(_extract_text(response)))

    def generate_content_brief(self, context: ContentBriefContext) -> ContentBriefResult:
        try:
            response = self.client.messages.create(
                model=CONTENT_MODEL,
                max_tokens=1024,
                temperature=0.6,
                system=CONTENT_BRIEF_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": self._build_content_brief_prompt(context)}],
            )
        except Exception as exc:
            raise AIProviderError(f"Claude request failed: {exc}") from exc

        return parse_content_brief_response(_extract_json(_extract_text(response)))

    def generate_content_piece(self, context: ContentPieceContext) -> ContentPieceResult:
        try:
            response = self.client.messages.create(
                model=CONTENT_MODEL,
                max_tokens=1024,
                temperature=0.7,
                system=content_piece_system_prompt(context.content_type),
                messages=[{"role": "user", "content": self._build_content_piece_prompt(context)}],
            )
        except Exception as exc:
            raise AIProviderError(f"Claude request failed: {exc}") from exc

        body = _extract_text(response).strip()
        if not body:
            raise AIProviderError("Claude returned an empty content body.")
        return ContentPieceResult(body=body)

    def chat_refine(self, context: ChatRefineContext) -> ChatRefineResult:
        try:
            response = self.client.messages.create(
                model=CONTENT_MODEL,
                max_tokens=1024,
                temperature=0.6,
                system=CHAT_REFINE_SYSTEM_PROMPT,
                messages=self._build_chat_history_messages(context),
            )
        except Exception as exc:
            raise AIProviderError(f"Claude request failed: {exc}") from exc

        reply = _extract_text(response).strip()
        if not reply:
            raise AIProviderError("Claude returned an empty reply.")
        return ChatRefineResult(reply=reply)
