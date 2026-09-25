from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.availability.api.v1.serializers.inline import (
    AvailabilityOrganizationInlineSerializer,
)
from apps.availability.models import Holiday


class HolidayReadSerializer(serializers.ModelSerializer):
    """Serializer for reading holiday details."""

    organization = AvailabilityOrganizationInlineSerializer(read_only=True)

    class Meta:
        model = Holiday
        fields = (
            "id",
            "organization",
            "date",
            "title",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class HolidayCreateSerializer(serializers.Serializer):
    """Serializer for creating a new holiday."""

    organization_id = serializers.UUIDField()
    date = serializers.DateField()
    title = serializers.CharField(max_length=255)
    is_active = serializers.BooleanField(required=False, default=True)

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(_("Holiday title is required."))
        return value


class HolidayUpdateSerializer(serializers.Serializer):
    """Serializer for updating a holiday."""

    date = serializers.DateField(required=False)
    title = serializers.CharField(max_length=255, required=False)
    is_active = serializers.BooleanField(required=False)

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(_("Holiday title cannot be empty."))
        return value
