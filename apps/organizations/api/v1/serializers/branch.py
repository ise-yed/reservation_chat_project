"""
Serializers for Branch model.

Handles validation and serialization for branch read, create, and update operations.
"""

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.organizations.models import Branch


class BranchReadSerializer(serializers.ModelSerializer):
    """Serializer for reading branch data with nested organization info."""

    organization_id = serializers.UUIDField(source="organization.id", read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = Branch
        fields = (
            "id",
            "organization_id",
            "organization_name",
            "name",
            "address",
            "phone_number",
            "latitude",
            "longitude",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class BranchCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new branch."""

    class Meta:
        model = Branch
        fields = (
            "name",
            "address",
            "phone_number",
            "latitude",
            "longitude",
            "is_active",
        )

    def validate_name(self, value):
        """Validate that branch name is not empty or whitespace-only."""
        value = value.strip()
        if not value:
            raise serializers.ValidationError(_("Branch name is required."))
        return value


class BranchUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a branch. All fields are optional."""

    class Meta:
        model = Branch
        fields = (
            "name",
            "address",
            "phone_number",
            "latitude",
            "longitude",
            "is_active",
        )
        extra_kwargs = {
            "name": {"required": False, "allow_blank": True},
            "address": {"required": False},
            "phone_number": {"required": False},
            "latitude": {"required": False},
            "longitude": {"required": False},
            "is_active": {"required": False},
        }

    def validate_name(self, value):
        """Validate name only if provided (not None) and not empty."""
        if value is not None:
            value = value.strip()
            if not value:
                raise serializers.ValidationError(_("Branch name cannot be empty."))
        return value
