from rest_framework import serializers

from apps.appointments.enums import AppointmentStatus
from apps.appointments.models import Appointment
from apps.offerings.models import Offering
from apps.organizations.models import Branch, Organization
from apps.providers.models import ProviderProfile
from apps.users.api.v1.serializers import UserReadSerializer


class AppointmentCreateSerializer(serializers.Serializer):
    provider_id = serializers.UUIDField()
    offering_id = serializers.UUIDField()
    start_at = serializers.DateTimeField()
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )


class AppointmentOrganizationInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = (
            "id",
            "name",
            "slug",
        )
        read_only_fields = fields


class AppointmentBranchInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = (
            "id",
            "name",
            "address",
            "phone_number",
        )
        read_only_fields = fields


class AppointmentProviderInlineSerializer(serializers.ModelSerializer):
    user = UserReadSerializer(read_only=True)

    class Meta:
        model = ProviderProfile
        fields = (
            "id",
            "user",
            "title",
            "specialty",
            "is_active",
        )
        read_only_fields = fields


class AppointmentOfferingInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offering
        fields = (
            "id",
            "title",
            "duration_minutes",
            "buffer_before_minutes",
            "buffer_after_minutes",
            "price",
            "requires_approval",
            "is_active",
        )
        read_only_fields = fields


class AppointmentCancelSerializer(serializers.Serializer):
    cancel_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )


class AppointmentStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.COMPLETED,
            AppointmentStatus.NO_SHOW,
        ]
    )


class AppointmentReadSerializer(serializers.ModelSerializer):
    organization = AppointmentOrganizationInlineSerializer(read_only=True)
    branch = AppointmentBranchInlineSerializer(read_only=True)
    customer = UserReadSerializer(read_only=True)
    provider = AppointmentProviderInlineSerializer(read_only=True)
    offering = AppointmentOfferingInlineSerializer(read_only=True)
    created_by = UserReadSerializer(read_only=True)
    cancelled_by = UserReadSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = (
            "id",
            "organization",
            "branch",
            "customer",
            "provider",
            "offering",
            "start_at",
            "end_at",
            "blocked_start_at",
            "blocked_end_at",
            "status",
            "price",
            "notes",
            "cancel_reason",
            "cancelled_by",
            "cancelled_at",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
