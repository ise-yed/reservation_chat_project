from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.appointments.models import Appointment
from apps.organizations.models import Organization
from apps.payments.enums import PaymentMethod
from apps.payments.models import Payment, PaymentTransaction
from apps.users.api.v1.serializers import UserReadSerializer


class PaymentOrganizationInlineSerializer(serializers.ModelSerializer):
    """Inline serializer for organization in payment."""

    class Meta:
        model = Organization
        fields = ("id", "name", "slug")
        read_only_fields = fields


class PaymentAppointmentInlineSerializer(serializers.ModelSerializer):
    """Inline serializer for appointment in payment."""

    customer = UserReadSerializer(read_only=True)
    offering_title = serializers.CharField(source="offering.title", read_only=True)
    provider_name = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = (
            "id",
            "customer",
            "offering_title",
            "provider_name",
            "start_at",
            "end_at",
            "status",
            "price",
        )
        read_only_fields = fields

    @extend_schema_field(field=serializers.CharField())
    def get_provider_name(self, obj):
        provider_user = obj.provider.user
        if hasattr(provider_user, "full_name") and provider_user.full_name:
            return provider_user.full_name
        return provider_user.email


class PaymentMarkPaidSerializer(serializers.Serializer):
    """Serializer for marking a payment as paid."""

    gateway_reference = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )
    raw_response = serializers.JSONField(required=False, default=dict)


class PaymentMarkFailedSerializer(serializers.Serializer):
    """Serializer for marking a payment as failed."""

    failure_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )
    gateway_reference = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )
    raw_response = serializers.JSONField(required=False, default=dict)


class PaymentRefundSerializer(serializers.Serializer):
    """Serializer for refunding a payment."""

    refund_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )


class AppointmentPaymentCreateSerializer(serializers.Serializer):
    """Serializer for creating a payment for an appointment."""

    appointment_id = serializers.UUIDField()
    method = serializers.ChoiceField(
        choices=PaymentMethod.choices,
        required=False,
        default=PaymentMethod.MOCK,
    )


class PaymentTransactionReadSerializer(serializers.ModelSerializer):
    """Serializer for reading payment transaction details."""

    class Meta:
        model = PaymentTransaction
        fields = (
            "id",
            "transaction_type",
            "amount",
            "status",
            "gateway_reference",
            "message",
            "raw_response",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class PaymentReadSerializer(serializers.ModelSerializer):
    """Serializer for reading payment details."""

    appointment = PaymentAppointmentInlineSerializer(read_only=True)
    organization = PaymentOrganizationInlineSerializer(read_only=True)
    payer = UserReadSerializer(read_only=True)
    created_by = UserReadSerializer(read_only=True)
    transactions = PaymentTransactionReadSerializer(many=True, read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "appointment",
            "organization",
            "payer",
            "amount",
            "currency",
            "status",
            "method",
            "gateway_reference",
            "idempotency_key",
            "paid_at",
            "failed_at",
            "cancelled_at",
            "refunded_at",
            "failure_reason",
            "refund_reason",
            "created_by",
            "data",
            "transactions",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
