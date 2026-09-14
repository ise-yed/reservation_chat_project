from rest_framework import serializers

from apps.availability.api.v1.serializers.inline import (
    AvailabilityProviderInlineSerializer,
)
from apps.availability.models import Weekday, WorkingHour


class WorkingHourReadSerializer(serializers.ModelSerializer):
    """Serializer for reading working hour details."""

    provider = AvailabilityProviderInlineSerializer(read_only=True)
    weekday_display = serializers.CharField(source="get_weekday_display", read_only=True)

    class Meta:
        model = WorkingHour
        fields = (
            "id",
            "provider",
            "weekday",
            "weekday_display",
            "start_time",
            "end_time",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class WorkingHourCreateSerializer(serializers.Serializer):
    """Serializer for creating a new working hour."""

    provider_id = serializers.UUIDField()
    weekday = serializers.ChoiceField(choices=Weekday.choices)
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    is_active = serializers.BooleanField(required=False, default=True)


class WorkingHourUpdateSerializer(serializers.Serializer):
    """Serializer for updating a working hour."""

    weekday = serializers.ChoiceField(choices=Weekday.choices, required=False)
    start_time = serializers.TimeField(required=False)
    end_time = serializers.TimeField(required=False)
    is_active = serializers.BooleanField(required=False)
