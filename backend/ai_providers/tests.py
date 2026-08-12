import json
from unittest.mock import MagicMock, patch

import pytest

from ai_providers.base import (
    AIProviderError,
    ChatRefineContext,
    ContentBriefContext,
    ContentPieceContext,
    TrendAnalysisContext,
    parse_analysis_response,
    parse_content_brief_response,
)
from ai_providers.claude_provider import ClaudeProvider
from ai_providers.factory import get_ai_provider
from ai_providers.openai_provider import OpenAIProvider

VALID_BRIEF_RESPONSE = {
    "business_angle": "Frame this as a shift in how businesses operate.",
    "founder_angle": "Founders can build tooling around this shift.",
    "educational_angle": "Explain the shift in plain terms for newcomers.",
    "marketing_angle": "Brands can tie campaigns to this shift.",
    "talking_points": ["Point one", "Point two", "Point three"],
    "content_angle": "A perspective-specific angle on this shift.",
}

VALID_RESPONSE = {
    "business_relevance": "Businesses should care because X.",
    "founder_relevance": "Founders should care because Y.",
    "entrepreneurship_relevance": "There's an opportunity here.",
    "ai_relevance": "Not directly AI-related.",
    "why_spreading": "It's spreading because Z.",
    "estimated_lifespan": "2-3 weeks",
    "trend_score": 72,
    "opportunity_score": 65,
    "confidence_score": 80,
    "content_creator_score": 80,
    "founder_score": 94,
    "investor_score": 60,
    "why_it_matters": "It matters because of Q.",
    "what_is_happening": "X just happened.",
    "trend_stage": "growing",
    "suggested_content_angle": "A concrete angle a creator could use.",
    "summary": "A neutral summary.",
    "category_suggestion": "Fintech",
}


class TestParseAnalysisResponse:
    def test_parses_a_valid_response(self):
        result = parse_analysis_response(VALID_RESPONSE)
        assert result.trend_score == 72
        assert result.category_suggestion == "Fintech"

    def test_missing_field_raises(self):
        data = {k: v for k, v in VALID_RESPONSE.items() if k != "trend_score"}
        with pytest.raises(AIProviderError):
            parse_analysis_response(data)

    def test_score_out_of_range_raises(self):
        data = {**VALID_RESPONSE, "trend_score": 150}
        with pytest.raises(AIProviderError):
            parse_analysis_response(data)

    def test_non_integer_score_raises(self):
        data = {**VALID_RESPONSE, "trend_score": "high"}
        with pytest.raises(AIProviderError):
            parse_analysis_response(data)

    def test_null_category_suggestion_becomes_none(self):
        data = {**VALID_RESPONSE, "category_suggestion": None}
        result = parse_analysis_response(data)
        assert result.category_suggestion is None

    def test_best_audience_is_computed_from_highest_score_not_trusted_from_ai(self):
        # founder_score (94) is highest in VALID_RESPONSE — even if the
        # AI's own JSON claimed something else, we never read a
        # "best_audience" key from it at all.
        data = {**VALID_RESPONSE, "best_audience": "investors"}
        result = parse_analysis_response(data)
        assert result.best_audience == "founders"

    def test_best_audience_picks_investors_when_investor_score_highest(self):
        data = {
            **VALID_RESPONSE,
            "content_creator_score": 50,
            "founder_score": 50,
            "investor_score": 99,
        }
        result = parse_analysis_response(data)
        assert result.best_audience == "investors"

    def test_best_audience_ties_break_deterministically(self):
        data = {
            **VALID_RESPONSE,
            "content_creator_score": 80,
            "founder_score": 80,
            "investor_score": 80,
        }
        result = parse_analysis_response(data)
        assert result.best_audience == "founders"

    def test_audience_score_out_of_range_raises(self):
        data = {**VALID_RESPONSE, "founder_score": 500}
        with pytest.raises(AIProviderError):
            parse_analysis_response(data)

    def test_trend_stage_is_normalized_to_lowercase(self):
        data = {**VALID_RESPONSE, "trend_stage": "Growing"}
        result = parse_analysis_response(data)
        assert result.trend_stage == "growing"

    def test_invalid_trend_stage_raises(self):
        data = {**VALID_RESPONSE, "trend_stage": "exploding"}
        with pytest.raises(AIProviderError):
            parse_analysis_response(data)


class TestParseContentBriefResponse:
    def test_parses_a_valid_response(self):
        result = parse_content_brief_response(VALID_BRIEF_RESPONSE)
        assert result.business_angle == "Frame this as a shift in how businesses operate."
        assert result.talking_points == ["Point one", "Point two", "Point three"]

    def test_missing_field_raises(self):
        data = {k: v for k, v in VALID_BRIEF_RESPONSE.items() if k != "business_angle"}
        with pytest.raises(AIProviderError):
            parse_content_brief_response(data)

    def test_talking_points_must_be_a_list(self):
        data = {**VALID_BRIEF_RESPONSE, "talking_points": "not a list"}
        with pytest.raises(AIProviderError):
            parse_content_brief_response(data)

    def test_content_angle_is_parsed(self):
        result = parse_content_brief_response(VALID_BRIEF_RESPONSE)
        assert result.content_angle == "A perspective-specific angle on this shift."

    def test_missing_content_angle_raises(self):
        data = {k: v for k, v in VALID_BRIEF_RESPONSE.items() if k != "content_angle"}
        with pytest.raises(AIProviderError):
            parse_content_brief_response(data)


class TestContentPerspectivePrompts:
    """Content Perspective must actually change what's sent to the
    model — these check the prompt text itself rather than a live
    response, since that's the one thing guaranteed to differ
    regardless of which provider/model answers it.
    """

    def test_content_piece_prompt_includes_perspective_when_set(self):
        founders_prompt = OpenAIProvider._build_content_piece_prompt(
            ContentPieceContext(
                trend_title="Test", content_type="hook", angle="An angle", perspective="founders"
            )
        )
        investors_prompt = OpenAIProvider._build_content_piece_prompt(
            ContentPieceContext(
                trend_title="Test", content_type="hook", angle="An angle", perspective="investors"
            )
        )
        assert "founders" in founders_prompt.lower()
        assert "investors" in investors_prompt.lower()
        assert founders_prompt != investors_prompt

    def test_content_piece_prompt_omits_perspective_section_when_blank(self):
        prompt = OpenAIProvider._build_content_piece_prompt(
            ContentPieceContext(trend_title="Test", content_type="hook", angle="An angle")
        )
        assert "Content Perspective" not in prompt

    def test_content_brief_prompt_includes_perspective_when_set(self):
        prompt = OpenAIProvider._build_content_brief_prompt(
            ContentBriefContext(trend_title="Test", perspective="investors")
        )
        assert "Content Perspective: investors" in prompt

    def test_content_brief_prompt_includes_intelligence_context(self):
        prompt = OpenAIProvider._build_content_brief_prompt(
            ContentBriefContext(
                trend_title="Test",
                trend_score=80,
                opportunity_score=70,
                best_audience="founders",
                why_it_matters="It matters a lot.",
                trend_stage="growing",
                estimated_lifespan="2-3 weeks",
            )
        )
        assert "80/100" in prompt
        assert "It matters a lot." in prompt
        assert "growing" in prompt


class TestFactory:
    def test_defaults_to_settings_ai_provider(self, settings):
        settings.AI_PROVIDER = "claude"
        provider = get_ai_provider()
        assert isinstance(provider, ClaudeProvider)

    def test_explicit_name_overrides_settings(self, settings):
        settings.AI_PROVIDER = "claude"
        provider = get_ai_provider("openai")
        assert isinstance(provider, OpenAIProvider)

    def test_unknown_provider_raises(self):
        with pytest.raises(AIProviderError):
            get_ai_provider("not-a-real-provider")


class TestOpenAIProvider:
    def test_raises_clearly_when_api_key_missing(self, settings):
        settings.OPENAI_API_KEY = ""
        provider = OpenAIProvider()
        with pytest.raises(AIProviderError):
            provider.generate_trend_analysis(TrendAnalysisContext(title="Test"))

    @patch("ai_providers.openai_provider.OpenAI")
    def test_parses_a_successful_response(self, mock_openai_cls, settings):
        settings.OPENAI_API_KEY = "sk-fake"
        import json

        mock_message = MagicMock(content=json.dumps(VALID_RESPONSE))
        mock_choice = MagicMock(message=mock_message)
        mock_openai_cls.return_value.chat.completions.create.return_value = MagicMock(
            choices=[mock_choice]
        )

        provider = OpenAIProvider()
        result = provider.generate_trend_analysis(TrendAnalysisContext(title="AI Regulation"))

        assert result.trend_score == 72

    @patch("ai_providers.openai_provider.OpenAI")
    def test_wraps_api_errors(self, mock_openai_cls, settings):
        settings.OPENAI_API_KEY = "sk-fake"
        mock_openai_cls.return_value.chat.completions.create.side_effect = RuntimeError("boom")

        provider = OpenAIProvider()
        with pytest.raises(AIProviderError):
            provider.generate_trend_analysis(TrendAnalysisContext(title="Test"))

    @patch("ai_providers.openai_provider.OpenAI")
    def test_generates_a_content_brief(self, mock_openai_cls, settings):
        settings.OPENAI_API_KEY = "sk-fake"
        mock_message = MagicMock(content=json.dumps(VALID_BRIEF_RESPONSE))
        mock_openai_cls.return_value.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=mock_message)]
        )

        provider = OpenAIProvider()
        result = provider.generate_content_brief(ContentBriefContext(trend_title="AI Regulation"))

        assert result.founder_angle == "Founders can build tooling around this shift."

    @patch("ai_providers.openai_provider.OpenAI")
    def test_generates_a_content_piece(self, mock_openai_cls, settings):
        settings.OPENAI_API_KEY = "sk-fake"
        mock_message = MagicMock(content="Three punchy hook lines here.")
        mock_openai_cls.return_value.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=mock_message)]
        )

        provider = OpenAIProvider()
        result = provider.generate_content_piece(
            ContentPieceContext(trend_title="AI Regulation", content_type="hook", angle="Founder")
        )

        assert result.body == "Three punchy hook lines here."

    def test_generate_content_piece_rejects_unknown_content_type(self, settings):
        settings.OPENAI_API_KEY = "sk-fake"
        provider = OpenAIProvider()
        with pytest.raises(AIProviderError):
            provider.generate_content_piece(
                ContentPieceContext(trend_title="Test", content_type="not-a-type", angle="x")
            )

    @patch("ai_providers.openai_provider.OpenAI")
    def test_chat_refine(self, mock_openai_cls, settings):
        settings.OPENAI_API_KEY = "sk-fake"
        mock_message = MagicMock(content="Here is the revised hook.")
        mock_openai_cls.return_value.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=mock_message)]
        )

        provider = OpenAIProvider()
        result = provider.chat_refine(
            ChatRefineContext(
                content_body="Original hook.",
                content_type="hook",
                instruction="Make it punchier.",
            )
        )

        assert result.reply == "Here is the revised hook."


class TestClaudeProvider:
    def test_raises_clearly_when_api_key_missing(self, settings):
        settings.ANTHROPIC_API_KEY = ""
        provider = ClaudeProvider()
        with pytest.raises(AIProviderError):
            provider.generate_trend_analysis(TrendAnalysisContext(title="Test"))

    @patch("ai_providers.claude_provider.Anthropic")
    def test_parses_a_successful_response(self, mock_anthropic_cls, settings):
        settings.ANTHROPIC_API_KEY = "fake"
        import json

        text_block = MagicMock(type="text", text=json.dumps(VALID_RESPONSE))
        mock_anthropic_cls.return_value.messages.create.return_value = MagicMock(
            content=[text_block]
        )

        provider = ClaudeProvider()
        result = provider.generate_trend_analysis(TrendAnalysisContext(title="AI Regulation"))

        assert result.opportunity_score == 65

    @patch("ai_providers.claude_provider.Anthropic")
    def test_strips_markdown_fencing_around_json(self, mock_anthropic_cls, settings):
        import json

        settings.ANTHROPIC_API_KEY = "fake"
        fenced = f"```json\n{json.dumps(VALID_RESPONSE)}\n```"
        text_block = MagicMock(type="text", text=fenced)
        mock_anthropic_cls.return_value.messages.create.return_value = MagicMock(
            content=[text_block]
        )

        provider = ClaudeProvider()
        result = provider.generate_trend_analysis(TrendAnalysisContext(title="Test"))

        assert result.trend_score == 72

    @patch("ai_providers.claude_provider.Anthropic")
    def test_generates_a_content_brief(self, mock_anthropic_cls, settings):
        settings.ANTHROPIC_API_KEY = "fake"
        text_block = MagicMock(type="text", text=json.dumps(VALID_BRIEF_RESPONSE))
        mock_anthropic_cls.return_value.messages.create.return_value = MagicMock(
            content=[text_block]
        )

        provider = ClaudeProvider()
        result = provider.generate_content_brief(ContentBriefContext(trend_title="AI Regulation"))

        assert result.marketing_angle == "Brands can tie campaigns to this shift."

    @patch("ai_providers.claude_provider.Anthropic")
    def test_generates_a_content_piece(self, mock_anthropic_cls, settings):
        settings.ANTHROPIC_API_KEY = "fake"
        text_block = MagicMock(type="text", text="Three punchy hook lines here.")
        mock_anthropic_cls.return_value.messages.create.return_value = MagicMock(
            content=[text_block]
        )

        provider = ClaudeProvider()
        result = provider.generate_content_piece(
            ContentPieceContext(trend_title="AI Regulation", content_type="hook", angle="Founder")
        )

        assert result.body == "Three punchy hook lines here."

    @patch("ai_providers.claude_provider.Anthropic")
    def test_chat_refine(self, mock_anthropic_cls, settings):
        settings.ANTHROPIC_API_KEY = "fake"
        text_block = MagicMock(type="text", text="Here is the revised hook.")
        mock_anthropic_cls.return_value.messages.create.return_value = MagicMock(
            content=[text_block]
        )

        provider = ClaudeProvider()
        result = provider.chat_refine(
            ChatRefineContext(
                content_body="Original hook.",
                content_type="hook",
                instruction="Make it punchier.",
            )
        )

        assert result.reply == "Here is the revised hook."
