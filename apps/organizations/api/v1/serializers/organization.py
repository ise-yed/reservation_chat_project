"""
Serializers for Organization model.

Handles validation and serialization for organization read, create, and update operations.
"""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.organizations.models import Organization
from apps.users.api.v1.serializers import UserReadSerializer


class OrganizationReadSerializer(serializers.ModelSerializer):
    """Serializer for reading organization data with nested owner and branch count."""

    owner = UserReadSerializer(read_only=True)
    active_branches_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = (
            "id",
            "owner",
            "name",
            "slug",
            "description",
            "phone_number",
            "email",
            "website",
            "timezone",
            "is_active",
            "active_branches_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    @extend_schema_field(field=serializers.IntegerField())
    def get_active_branches_count(self, obj):
        """Return active branches count from annotation or calculate directly."""
        return getattr(
            obj,
            "active_branches_count",
            obj.branches.filter(is_active=True).count(),
        )


class OrganizationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new organization. Slug is optional."""

    slug = serializers.SlugField(
        max_length=140,
        allow_unicode=True,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = Organization
        fields = (
            "name",
            "slug",
            "description",
            "phone_number",
            "email",
            "website",
            "timezone",
            "is_active",
        )

    def validate_name(self, value):
        """Validate that organization name is not empty or whitespace-only."""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Organization name is required.")
        return value


class OrganizationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an organization. All fields are optional."""

    slug = serializers.SlugField(
        max_length=140,
        allow_unicode=True,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = Organization
        fields = (
            "name",
            "slug",
            "description",
            "phone_number",
            "email",
            "website",
            "timezone",
            "is_active",
        )
        extra_kwargs = {
            "name": {"required": False, "allow_blank": True},
            "description": {"required": False},
            "phone_number": {"required": False},
            "email": {"required": False},
            "website": {"required": False},
            "timezone": {"required": False},
            "is_active": {"required": False},
        }

    def validate_name(self, value):
        """Validate name only if provided (not None) and not empty."""
        if value is not None:
            value = value.strip()
            if not value:
                raise serializers.ValidationError("Organization name cannot be empty.")
        return value
