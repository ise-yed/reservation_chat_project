"""
Inline serializers for availability app.
"""

from rest_framework import serializers

from apps.categories.models import Category
from apps.organizations.models import Organization
from apps.providers.models import ProviderProfile
from apps.users.api.v1.serializers import UserReadSerializer


class AvailabilityOrganizationInlineSerializer(serializers.ModelSerializer):
    """Inline serializer for organization in availability."""

    class Meta:
        model = Organization
        fields = (
            "id",
            "name",
            "slug",
        )
        read_only_fields = fields


class AvailabilitySpecialtyInlineSerializer(serializers.ModelSerializer):
    """Inline serializer for specialty in availability."""

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
        )
        read_only_fields = fields


class AvailabilityProviderInlineSerializer(serializers.ModelSerializer):
    """Inline serializer for provider in availability."""

    user = UserReadSerializer(read_only=True)
    organization = AvailabilityOrganizationInlineSerializer(read_only=True)
    specialties = AvailabilitySpecialtyInlineSerializer(many=True, read_only=True)

    class Meta:
        model = ProviderProfile
        fields = (
            "id",
            "user",
            "organization",
            "title",
            "specialties",
            "is_active",
        )
        read_only_fields = fields
