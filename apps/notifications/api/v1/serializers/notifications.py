from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notification read operations."""

    class Meta:
        model = Notification
        fields = (
            "id",
            "type",
            "title",
            "message",
            "is_read",
            "read_at",
            "related_object_type",
            "related_object_id",
            "data",
            "created_at",
        )
        read_only_fields = fields
