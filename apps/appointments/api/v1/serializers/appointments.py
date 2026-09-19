"""
Serializers for appointment operations.
"""


from rest_framework import serializers

from apps.appointments.enums import AppointmentStatus
from apps.appointments.models import Appointment
from apps.categories.models import Category
from apps.offerings.models import Offering
from apps.organizations.models import Branch, Organization
from apps.payments.api.v1.serializers import PaymentReadSerializer
from apps.payments.enums import PaymentMethod
from apps.providers.models import ProviderProfile
from apps.users.api.v1.serializers import UserReadSerializer


class AppointmentCreateSerializer(serializers.Serializer):
    """Serializer for creating an appointment."""


    provider_id = serializers.UUIDField()
    offering_id = serializers.UUIDField()
    start_at = serializers.DateTimeField()
    payment_method = serializers.ChoiceField(
        choices=PaymentMethod.choices,
        required=False,
        default=PaymentMethod.ONLINE,
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )



class AppointmentOrganizationInlineSerializer(serializers.ModelSerializer):
    """Inline serializer for organization summary."""


    class Meta:
        model = Organization
        fields = (
            "id",
            "name",
            "slug",
        )
        read_only_fields = fields



class AppointmentBranchInlineSerializer(serializers.ModelSerializer):
    """Inline serializer for branch summary."""


    class Meta:
        model = Branch
        fields = (
            "id",
            "name",
            "address",
            "phone_number",
        )
        read_only_fields = fields



class AppointmentSpecialtyInlineSerializer(serializers.ModelSerializer):
    """Inline serializer for specialty summary."""


    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
        )
        read_only_fields = fields



class AppointmentProviderInlineSerializer(serializers.ModelSerializer):
    """Inline serializer for provider summary."""


    user = UserReadSerializer(read_only=True)
    specialties = AppointmentSpecialtyInlineSerializer(many=True, read_only=True)


    class Meta:
        model = ProviderProfile
        fields = (
            "id",
            "user",
            "title",
            "specialties",
            "is_active",
        )
        read_only_fields = fields



class AppointmentOfferingInlineSerializer(serializers.ModelSerializer):
    """Inline serializer for offering summary."""


    class Meta:
        model = Offering
        fields = (
            "id",
            "title",
            "visit_mode",
            "duration_minutes",
            "buffer_before_minutes",
            "buffer_after_minutes",
            "price",
            "requires_approval",
            "is_active",
        )
        read_only_fields = fields



class AppointmentCancelSerializer(serializers.Serializer):
    """Serializer for cancelling an appointment."""


    cancel_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )



class AppointmentStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating appointment status."""


    status = serializers.ChoiceField(
        choices=[
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.COMPLETED,
            AppointmentStatus.NO_SHOW,
        ]
    )



class AppointmentReadSerializer(serializers.ModelSerializer):
    """Serializer for reading complete appointment details."""


    organization = AppointmentOrganizationInlineSerializer(read_only=True)
    branch = AppointmentBranchInlineSerializer(read_only=True)
    customer = UserReadSerializer(read_only=True)
    provider = AppointmentProviderInlineSerializer(read_only=True)
    offering = AppointmentOfferingInlineSerializer(read_only=True)
    created_by = UserReadSerializer(read_only=True)
    cancelled_by = UserReadSerializer(read_only=True)
    payment = PaymentReadSerializer(read_only=True, allow_null=True)


    class Meta:
        model = Appointment
        fields = (
            "id",
            "organization",
            "branch",
            "customer",
            "provider",
            "offering",
            "visit_mode",
            "start_at",
            "end_at",
            "blocked_start_at",
            "blocked_end_at",
            "status",
            "price",
            "payment",
            "notes",
            "cancel_reason",
            "cancelled_by",
            "cancelled_at",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
