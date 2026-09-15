"""
Inline serializers for organization, branch, and specialty summaries.
"""

from rest_framework import serializers

from apps.categories.models import Category
from apps.organizations.models import Branch, Organization
from apps.providers.models import ProviderProfile
from apps.users.api.v1.serializers import UserReadSerializer


class ProviderOrganizationInlineSerializer(serializers.ModelSerializer):
    """Inline serializer for organization summary in provider profile."""

    class Meta:
        model = Organization
        fields = (
            "id",
            "name",
            "slug",
        )
        read_only_fields = fields


class ProviderBranchInlineSerializer(serializers.ModelSerializer):
    """Inline serializer for branch summary in provider profile."""

    class Meta:
        model = Branch
        fields = (
            "id",
            "name",
            "address",
            "phone_number",
        )
        read_only_fields = fields


class ProviderSpecialtyInlineSerializer(serializers.ModelSerializer):
    """Inline serializer for specialty summary in provider profile."""

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
        )
        read_only_fields = fields


class ProviderProfileCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a new provider profile.

    Uses Serializer instead of ModelSerializer for explicit control over validation.
    """

    user_id = serializers.UUIDField()
    organization_id = serializers.UUIDField()
    branch_id = serializers.UUIDField(required=False, allow_null=True)

    title = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
        default="",
    )

    specialty_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list,
    )

    bio = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )
    default_slot_duration_minutes = serializers.IntegerField(
        required=False,
        default=30,
        min_value=1,
        max_value=480,
    )
    is_active = serializers.BooleanField(required=False, default=True)

    def validate_title(self, value):
        """Strip whitespace from title if provided."""
        if value:
            value = value.strip()
        return value


class ProviderProfileReadSerializer(serializers.ModelSerializer):
    """
    Serializer for reading provider profile with nested user, organization, and specialties data.
    """

    user = UserReadSerializer(read_only=True)
    organization = ProviderOrganizationInlineSerializer(read_only=True)
    branch = ProviderBranchInlineSerializer(read_only=True)
    specialties = ProviderSpecialtyInlineSerializer(many=True, read_only=True)

    class Meta:
        model = ProviderProfile
        fields = (
            "id",
            "user",
            "organization",
            "branch",
            "title",
            "specialties",
            "bio",
            "default_slot_duration_minutes",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class ProviderProfileUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating a provider profile.

    All fields are optional to support partial updates (PATCH).
    """

    branch_id = serializers.UUIDField(required=False, allow_null=True)

    title = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
    )

    specialty_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
    )

    bio = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    default_slot_duration_minutes = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=480,
    )
    is_active = serializers.BooleanField(required=False)

    def validate_title(self, value):
        """Strip whitespace from title if provided."""
        if value:
            value = value.strip()
        return value
