from rest_framework import serializers

from apps.core.models import AIJob


class AIJobSerializer(serializers.ModelSerializer):
    can_retry = serializers.SerializerMethodField()

    class Meta:
        model = AIJob
        fields = (
            "id",
            "job_type",
            "status",
            "result",
            "error_message",
            "attempt_count",
            "can_retry",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_can_retry(self, job):
        return job.status == AIJob.Status.FAILED
