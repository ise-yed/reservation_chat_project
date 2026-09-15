from rest_framework import serializers

from apps.categories.api.v1.serializers import CategorySerializer
from apps.offerings.models import Offering
from apps.organizations.models import Organization
from apps.providers.models import ProviderProfile
from apps.users.api.v1.serializers import UserReadSerializer


class OfferingOrganizationInlineSerializer(serializers.ModelSerializer):
    """Inline serializer for organization in offering."""

    class Meta:
        model = Organization
        fields = (
            "id",
            "name",
            "slug",
        )
        read_only_fields = fields


class OfferingProviderInlineSerializer(serializers.ModelSerializer):
    """Inline serializer for provider in offering."""

    user = UserReadSerializer(read_only=True)
    specialties = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = ProviderProfile
        fields = (
            "id",
            "user",
            "title",
            "specialties",
            "default_slot_duration_minutes",
            "is_active",
        )
        read_only_fields = fields


class OfferingCreateSerializer(serializers.Serializer):
    """Serializer for creating a new offering."""

    organization_id = serializers.UUIDField()
    provider_id = serializers.UUIDField()

    title = serializers.CharField(max_length=255)
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )

    duration_minutes = serializers.IntegerField(
        required=False,
        default=30,
        min_value=1,
        max_value=480,
    )
    buffer_before_minutes = serializers.IntegerField(
        required=False,
        default=0,
        min_value=0,
        max_value=240,
    )
    buffer_after_minutes = serializers.IntegerField(
        required=False,
        default=0,
        min_value=0,
        max_value=240,
    )

    price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        default=0,
        min_value=0,
    )
    requires_approval = serializers.BooleanField(required=False, default=False)
    is_active = serializers.BooleanField(required=False, default=True)

    def validate_title(self, value):
        """Ensure title is not empty or just whitespace."""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Offering title is required.")
        return value


class OfferingReadSerializer(serializers.ModelSerializer):
    """Serializer for reading offering details."""

    organization = OfferingOrganizationInlineSerializer(read_only=True)
    provider = OfferingProviderInlineSerializer(read_only=True)
    category = CategorySerializer(read_only=True, allow_null=True, default=None)

    class Meta:
        model = Offering
        fields = (
            "id",
            "organization",
            "provider",
            "category",
            "title",
            "description",
            "duration_minutes",
            "buffer_before_minutes",
            "buffer_after_minutes",
            "price",
            "requires_approval",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class OfferingUpdateSerializer(serializers.Serializer):
    """Serializer for updating an offering."""

    title = serializers.CharField(
        max_length=255,
        required=False,
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    duration_minutes = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=480,
    )
    buffer_before_minutes = serializers.IntegerField(
        required=False,
        min_value=0,
        max_value=240,
    )
    buffer_after_minutes = serializers.IntegerField(
        required=False,
        min_value=0,
        max_value=240,
    )

    price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        min_value=0,
    )
    requires_approval = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)

    def validate_title(self, value):
        """Ensure updated title is not empty or just whitespace."""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Offering title cannot be empty.")
        return value
