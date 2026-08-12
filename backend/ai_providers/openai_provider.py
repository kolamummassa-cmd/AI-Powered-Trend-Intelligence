import json

from django.conf import settings
from openai import OpenAI

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

# Deliberately a fast/cheap model — trend scoring runs on every new
# trend detected and is closer to classification than creative
# writing. Content generation below uses a stronger model since
# writing quality is what the user actually judges there.
SCORING_MODEL = "gpt-4o-mini"
CONTENT_MODEL = "gpt-4o"


class OpenAIProvider(AIProvider):
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not settings.OPENAI_API_KEY:
                raise AIProviderError("OPENAI_API_KEY is not configured.")
            self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    def generate_trend_analysis(self, context: TrendAnalysisContext) -> TrendAnalysisResult:
        try:
            response = self.client.chat.completions.create(
                model=SCORING_MODEL,
                response_format={"type": "json_object"},
                temperature=0.3,
                messages=[
                    {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                    {"role": "user", "content": self._build_user_prompt(context)},
                ],
            )
        except Exception as exc:
            raise AIProviderError(f"OpenAI request failed: {exc}") from exc

        content = response.choices[0].message.content
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AIProviderError(f"OpenAI returned non-JSON content: {content[:200]}") from exc

        return parse_analysis_response(data)

    def generate_content_brief(self, context: ContentBriefContext) -> ContentBriefResult:
        try:
            response = self.client.chat.completions.create(
                model=CONTENT_MODEL,
                response_format={"type": "json_object"},
                temperature=0.6,
                messages=[
                    {"role": "system", "content": CONTENT_BRIEF_SYSTEM_PROMPT},
                    {"role": "user", "content": self._build_content_brief_prompt(context)},
                ],
            )
        except Exception as exc:
            raise AIProviderError(f"OpenAI request failed: {exc}") from exc

        content = response.choices[0].message.content
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AIProviderError(f"OpenAI returned non-JSON content: {content[:200]}") from exc

        return parse_content_brief_response(data)

    def generate_content_piece(self, context: ContentPieceContext) -> ContentPieceResult:
        try:
            response = self.client.chat.completions.create(
                model=CONTENT_MODEL,
                temperature=0.7,
                messages=[
                    {
                        "role": "system",
                        "content": content_piece_system_prompt(context.content_type),
                    },
                    {"role": "user", "content": self._build_content_piece_prompt(context)},
                ],
            )
        except Exception as exc:
            raise AIProviderError(f"OpenAI request failed: {exc}") from exc

        body = (response.choices[0].message.content or "").strip()
        if not body:
            raise AIProviderError("OpenAI returned an empty content body.")
        return ContentPieceResult(body=body)

    def chat_refine(self, context: ChatRefineContext) -> ChatRefineResult:
        try:
            response = self.client.chat.completions.create(
                model=CONTENT_MODEL,
                temperature=0.6,
                messages=[
                    {"role": "system", "content": CHAT_REFINE_SYSTEM_PROMPT},
                    *self._build_chat_history_messages(context),
                ],
            )
        except Exception as exc:
            raise AIProviderError(f"OpenAI request failed: {exc}") from exc

        reply = (response.choices[0].message.content or "").strip()
        if not reply:
            raise AIProviderError("OpenAI returned an empty reply.")
        return ChatRefineResult(reply=reply)
