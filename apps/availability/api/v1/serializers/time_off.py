from rest_framework import serializers

from apps.availability.api.v1.serializers.inline import (
    AvailabilityProviderInlineSerializer,
)
from apps.availability.models import TimeOff


class TimeOffReadSerializer(serializers.ModelSerializer):
    """Serializer for reading time off details."""

    provider = AvailabilityProviderInlineSerializer(read_only=True)

    class Meta:
        model = TimeOff
        fields = (
            "id",
            "provider",
            "start_at",
            "end_at",
            "reason",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class TimeOffCreateSerializer(serializers.Serializer):
    """Serializer for creating a new time off."""

    provider_id = serializers.UUIDField()
    start_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField()
    reason = serializers.CharField(required=False, allow_blank=True, default="")
    is_active = serializers.BooleanField(required=False, default=True)


class TimeOffUpdateSerializer(serializers.Serializer):
    """Serializer for updating a time off."""

    start_at = serializers.DateTimeField(required=False)
    end_at = serializers.DateTimeField(required=False)
    reason = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
