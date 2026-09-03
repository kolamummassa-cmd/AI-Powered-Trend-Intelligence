from django.conf import settings

from ai_providers.base import AIProvider, AIProviderError

_PROVIDERS = {
    "openai": "ai_providers.openai_provider.OpenAIProvider",
    "claude": "ai_providers.claude_provider.ClaudeProvider",
    "gemini": "ai_providers.gemini_provider.GeminiProvider",
}


def get_ai_provider(name: str | None = None) -> AIProvider:
    """Returns a ready-to-use AIProvider. Defaults to settings.AI_PROVIDER
    so call sites don't hardcode a vendor — override `name` only for
    things like an explicit A/B comparison between providers.
    """
    key = (name or settings.AI_PROVIDER or "").lower()
    try:
        dotted_path = _PROVIDERS[key]
    except KeyError:
        raise AIProviderError(f"Unknown AI provider '{key}'. Available: {sorted(_PROVIDERS)}")

    module_path, class_name = dotted_path.rsplit(".", 1)
    from importlib import import_module

    module = import_module(module_path)
    provider_cls = getattr(module, class_name)
    return provider_cls()
