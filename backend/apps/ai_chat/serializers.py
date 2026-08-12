from rest_framework import serializers

from apps.ai_chat.models import AIChatMessage
from apps.ai_chat.services import PLATFORM_CONVERSION_INSTRUCTIONS


class AIChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIChatMessage
        fields = ("id", "content", "role", "message", "created_at")
        read_only_fields = ("id", "content", "role", "message", "created_at")


class RefineContentRequestSerializer(serializers.Serializer):
    content_id = serializers.UUIDField()
    instruction = serializers.CharField(max_length=2000)


class ConvertContentRequestSerializer(serializers.Serializer):
    content_id = serializers.UUIDField()
    platform = serializers.ChoiceField(choices=list(PLATFORM_CONVERSION_INSTRUCTIONS.keys()))
