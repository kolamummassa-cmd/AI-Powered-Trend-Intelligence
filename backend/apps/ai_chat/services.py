from ai_providers import get_ai_provider
from ai_providers.base import ChatRefineContext
from apps.ai_chat.models import AIChatMessage, ChatRole
from apps.content_studio.models import GeneratedContent

# Platform-conversion is just a canned instruction fed through the
# same refine_content path — a user typing the same words would get
# the same result, this is purely a one-click convenience.
PLATFORM_CONVERSION_INSTRUCTIONS = {
    "linkedin": (
        "Rewrite this as a LinkedIn post: professional tone, short paragraphs, end with a "
        "question that invites comments."
    ),
    "twitter_thread": (
        "Rewrite this as a Twitter/X thread: number each tweet like '1/', '2/', etc., and keep "
        "each one under 280 characters."
    ),
    "carousel": (
        "Rewrite this as a slide-by-slide outline for an Instagram/LinkedIn carousel: one short "
        "idea per slide, 5-8 slides, numbered."
    ),
    "shorts_script": (
        "Rewrite this as a script for a vertical short-form video (Shorts/Reels/TikTok): a fast "
        "hook in the first line, punchy delivery throughout."
    ),
}


def _history_for(content: GeneratedContent) -> list[tuple[str, str]]:
    return [(msg.role, msg.message) for msg in content.chat_messages.all()]


def refine_content(
    content: GeneratedContent,
    instruction: str,
    user=None,
    provider_name: str | None = None,
) -> AIChatMessage:
    """Runs one refinement turn: sends the instruction plus the thread
    history to the AI provider, records both sides of the exchange,
    and updates the content body in place (refinement edits the
    current draft — regenerating a new version is a separate, explicit
    Content Studio action, not something a chat message triggers).
    """
    provider = get_ai_provider(provider_name)
    context = ChatRefineContext(
        content_body=content.body,
        content_type=content.content_type,
        instruction=instruction,
        history=_history_for(content),
    )
    result = provider.chat_refine(context)

    AIChatMessage.objects.create(content=content, role=ChatRole.USER, message=instruction)
    assistant_message = AIChatMessage.objects.create(
        content=content, role=ChatRole.ASSISTANT, message=result.reply
    )

    content.body = result.reply
    content.save(update_fields=["body", "updated_at"])

    return assistant_message


def convert_for_platform(
    content: GeneratedContent,
    platform: str,
    user=None,
    provider_name: str | None = None,
) -> AIChatMessage:
    instruction = PLATFORM_CONVERSION_INSTRUCTIONS.get(platform)
    if not instruction:
        raise ValueError(f"Unknown platform conversion: {platform!r}")

    return refine_content(
        content,
        instruction=f"Convert this content for {platform.replace('_', ' ')}. {instruction}",
        user=user,
        provider_name=provider_name,
    )
