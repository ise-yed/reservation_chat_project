from rest_framework import serializers

from apps.audit.models import AuditLog
from apps.organizations.models import Organization
from apps.users.api.v1.serializers import UserReadSerializer


class AuditOrganizationInlineSerializer(serializers.ModelSerializer):
    """Inline serializer for organization in audit log."""

    class Meta:
        model = Organization
        fields = (
            "id",
            "name",
            "slug",
        )
        read_only_fields = fields


class AuditLogReadSerializer(serializers.ModelSerializer):
    """Serializer for reading audit log details."""

    actor = UserReadSerializer(read_only=True)
    organization = AuditOrganizationInlineSerializer(read_only=True)

    class Meta:
        model = AuditLog
        fields = (
            "id",
            "actor",
            "organization",
            "action",
            "status",
            "target_object_type",
            "target_object_id",
            "target_object_repr",
            "ip_address",
            "user_agent",
            "metadata",
            "error_message",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
