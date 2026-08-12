from django.db import models

from apps.content_studio.models import GeneratedContent
from apps.core.models import BaseModel


class ChatRole(models.TextChoices):
    USER = "user", "User"
    ASSISTANT = "assistant", "Assistant"


class AIChatMessage(BaseModel):
    """One turn in the refinement thread attached to a GeneratedContent
    piece. Kept as a flat chronological log (not paired request/reply
    rows) so rendering the thread is just `content.chat_messages.all()`
    in order, and so a platform-conversion action (which is really just
    a canned instruction) shows up in the same history as a free-typed
    instruction.
    """

    content = models.ForeignKey(
        GeneratedContent, on_delete=models.CASCADE, related_name="chat_messages"
    )
    role = models.CharField(max_length=20, choices=ChatRole.choices)
    message = models.TextField()

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["content", "created_at"])]

    def __str__(self):
        return f"{self.role}: {self.message[:50]}"
