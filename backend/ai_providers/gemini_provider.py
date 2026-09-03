import json
import re

import requests
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


_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


class GeminiProvider(AIProvider):
    """Gemini Developer API provider.

    Uses the HTTPS API directly because ``requests`` is already a backend
    dependency. That keeps local setup simple: a GEMINI_API_KEY is the only
    extra value needed in ``backend/.env``.
    """

    api_base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    @property
    def api_key(self) -> str:
        if not settings.GEMINI_API_KEY:
            raise AIProviderError("GEMINI_API_KEY is not configured.")
        return settings.GEMINI_API_KEY

    def _generate(
        self,
        *,
        model: str,
        system_prompt: str,
        contents: list[dict],
        temperature: float,
        json_response: bool = False,
    ) -> str:
        generation_config = {
            "temperature": temperature,
            "maxOutputTokens": 1024,
        }
        if json_response:
            generation_config["responseMimeType"] = "application/json"

        try:
            response = requests.post(
                f"{self.api_base_url}/{model}:generateContent",
                params={"key": self.api_key},
                json={
                    "systemInstruction": {"parts": [{"text": system_prompt}]},
                    "contents": contents,
                    "generationConfig": generation_config,
                },
                timeout=60,
            )
            if not response.ok:
                try:
                    error_message = response.json().get("error", {}).get("message", "")
                except ValueError:
                    error_message = ""
                detail = error_message or "Gemini rejected the request."
                raise AIProviderError(
                    f"Gemini model '{model}' request failed "
                    f"(HTTP {response.status_code}): {detail[:300]}"
                )
            payload = response.json()
            parts = payload["candidates"][0]["content"]["parts"]
            text = "".join(part.get("text", "") for part in parts).strip()
        except requests.RequestException as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            detail = f"HTTP {status_code}" if status_code else type(exc).__name__
            raise AIProviderError(f"Gemini request failed ({detail}).") from exc
        except AIProviderError:
            raise
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise AIProviderError("Gemini returned an unexpected response.") from exc

        if not text:
            raise AIProviderError("Gemini returned an empty response.")
        return text

    @staticmethod
    def _parse_json(text: str) -> dict:
        match = _JSON_BLOCK.search(text)
        json_text = match.group(0) if match else text
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise AIProviderError(f"Gemini returned non-JSON content: {text[:200]}") from exc

    def generate_trend_analysis(self, context: TrendAnalysisContext) -> TrendAnalysisResult:
        text = self._generate(
            model=settings.GEMINI_SCORING_MODEL,
            system_prompt=ANALYSIS_SYSTEM_PROMPT,
            contents=[{"role": "user", "parts": [{"text": self._build_user_prompt(context)}]}],
            temperature=0.3,
            json_response=True,
        )
        return parse_analysis_response(self._parse_json(text))

    def generate_content_brief(self, context: ContentBriefContext) -> ContentBriefResult:
        text = self._generate(
            model=settings.GEMINI_CONTENT_MODEL,
            system_prompt=CONTENT_BRIEF_SYSTEM_PROMPT,
            contents=[
                {"role": "user", "parts": [{"text": self._build_content_brief_prompt(context)}]}
            ],
            temperature=0.6,
            json_response=True,
        )
        return parse_content_brief_response(self._parse_json(text))

    def generate_content_piece(self, context: ContentPieceContext) -> ContentPieceResult:
        text = self._generate(
            model=settings.GEMINI_CONTENT_MODEL,
            system_prompt=content_piece_system_prompt(context.content_type),
            contents=[
                {"role": "user", "parts": [{"text": self._build_content_piece_prompt(context)}]}
            ],
            temperature=0.7,
        )
        return ContentPieceResult(body=text)

    def chat_refine(self, context: ChatRefineContext) -> ChatRefineResult:
        contents = [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            f"Here is the current content ({context.content_type}):\n\n"
                            f"{context.content_body}"
                        )
                    }
                ],
            }
        ]
        for role, message in context.history:
            contents.append(
                {
                    "role": "model" if role == "assistant" else "user",
                    "parts": [{"text": message}],
                }
            )
        contents.append({"role": "user", "parts": [{"text": context.instruction}]})
        text = self._generate(
            model=settings.GEMINI_CONTENT_MODEL,
            system_prompt=CHAT_REFINE_SYSTEM_PROMPT,
            contents=contents,
            temperature=0.6,
        )
        return ChatRefineResult(reply=text)
