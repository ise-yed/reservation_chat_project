import uuid

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.appointments.models import Appointment
from apps.payments.enums import (
    PaymentMethod,
    PaymentStatus,
    PaymentTransactionType,
)
from apps.payments.models import Payment, PaymentTransaction
from apps.payments.permissions import (
    can_create_payment_for_appointment,
    can_manage_payment,
)
from apps.payments.services.helpers import (
    validate_appointment_is_payable,
    validate_payment_can_be_cancelled,
    validate_payment_can_be_paid,
    validate_payment_can_be_refunded,
    validate_payment_can_fail,
)
from apps.payments.services.notification import (
    publish_payment_failed_notification,
    publish_payment_success_notification,
    publish_refund_success_notification,
)


def _build_idempotency_key(*, appointment_id, method: str) -> str:
    """Build idempotency key for payment."""
    return f"appointment:{appointment_id}:method:{method}"


def _create_payment_transaction(
    *,
    payment,
    transaction_type,
    amount,
    status="success",
    gateway_reference="",
    message="",
    raw_response=None,
) -> PaymentTransaction:
    """Create a payment transaction record."""
    return PaymentTransaction.objects.create(
        payment=payment,
        transaction_type=transaction_type,
        amount=amount,
        status=status,
        gateway_reference=gateway_reference,
        message=message,
        raw_response=raw_response or {},
    )


@transaction.atomic
def initiate_appointment_payment(
    *,
    actor,
    appointment_id,
    method: str = PaymentMethod.MOCK,
) -> Payment:
    """Initiate a payment for an appointment."""
    appointment = (
        Appointment.objects.select_for_update(of=("self",))
        .select_related(
            "organization",
            "customer",
            "provider",
            "provider__user",
            "offering",
        )
        .get(id=appointment_id)
    )

    if not can_create_payment_for_appointment(actor, appointment):
        raise PermissionDenied("You are not allowed to create payment for this appointment.")

    validate_appointment_is_payable(appointment=appointment)

    existing_payment = (
        Payment.objects.filter(
            appointment=appointment,
            status__in=[
                PaymentStatus.PENDING,
                PaymentStatus.PAID,
            ],
        )
        .order_by("-created_at")
        .first()
    )

    if existing_payment:
        return existing_payment

    idempotency_key = _build_idempotency_key(
        appointment_id=appointment.id,
        method=method,
    )

    try:
        payment = Payment.objects.create(
            appointment=appointment,
            organization=appointment.organization,
            payer=appointment.customer,
            amount=appointment.price,
            currency="IRR",
            status=PaymentStatus.PENDING,
            method=method,
            idempotency_key=idempotency_key,
            created_by=actor,
            data={
                "appointment_id": str(appointment.id),
                "offering_id": str(appointment.offering_id),
            },
        )
    except IntegrityError as exc:
        payment = Payment.objects.filter(idempotency_key=idempotency_key).first()
        if payment:
            return payment

        raise ValidationError(
            {"appointment_id": ["Could not create payment for this appointment."]}
        ) from exc

    _create_payment_transaction(
        payment=payment,
        transaction_type=PaymentTransactionType.INITIATED,
        amount=payment.amount,
        message="Payment initiated.",
    )

    
    return payment


@transaction.atomic
def mark_payment_as_paid(
    *,
    payment,
    actor,
    gateway_reference: str = "",
    raw_response=None,
) -> Payment:
    """Mark a payment as paid."""
    locked_payment = (
        Payment.objects.select_for_update(of=("self",))
        .select_related(
            "appointment",
            "appointment__customer",
            "appointment__provider",
            "appointment__provider__user",
            "appointment__offering",
            "organization",
            "payer",
        )
        .get(id=payment.id)
    )

    if not can_manage_payment(actor, locked_payment):
        raise PermissionDenied("You are not allowed to mark this payment as paid.")

    validate_payment_can_be_paid(payment=locked_payment)

    locked_payment.status = PaymentStatus.PAID
    locked_payment.paid_at = timezone.now()
    locked_payment.gateway_reference = gateway_reference or f"mock-{uuid.uuid4()}"
    locked_payment.failure_reason = ""
    locked_payment.save(
        update_fields=[
            "status",
            "paid_at",
            "gateway_reference",
            "failure_reason",
            "updated_at",
        ]
    )

    _create_payment_transaction(
        payment=locked_payment,
        transaction_type=PaymentTransactionType.PAID,
        amount=locked_payment.amount,
        gateway_reference=locked_payment.gateway_reference,
        message="Payment marked as paid.",
        raw_response=raw_response,
    )

    publish_payment_success_notification(payment=locked_payment)

   
    return locked_payment


@transaction.atomic
def mark_payment_as_failed(
    *,
    payment,
    actor,
    failure_reason: str = "",
    gateway_reference: str = "",
    raw_response=None,
) -> Payment:
    """Mark a payment as failed."""
    locked_payment = (
        Payment.objects.select_for_update(of=("self",))
        .select_related(
            "appointment",
            "appointment__customer",
            "appointment__provider",
            "appointment__provider__user",
            "appointment__offering",
            "organization",
            "payer",
        )
        .get(id=payment.id)
    )

    if not can_manage_payment(actor, locked_payment):
        raise PermissionDenied("You are not allowed to mark this payment as failed.")

    validate_payment_can_fail(payment=locked_payment)

    locked_payment.status = PaymentStatus.FAILED
    locked_payment.failed_at = timezone.now()
    locked_payment.failure_reason = failure_reason.strip()
    locked_payment.gateway_reference = gateway_reference
    locked_payment.save(
        update_fields=[
            "status",
            "failed_at",
            "failure_reason",
            "gateway_reference",
            "updated_at",
        ]
    )

    _create_payment_transaction(
        payment=locked_payment,
        transaction_type=PaymentTransactionType.FAILED,
        amount=locked_payment.amount,
        status="failed",
        gateway_reference=gateway_reference,
        message=locked_payment.failure_reason,
        raw_response=raw_response,
    )

    publish_payment_failed_notification(payment=locked_payment)

    
    return locked_payment


@transaction.atomic
def cancel_payment(
    *,
    payment,
    actor,
) -> Payment:
    """Cancel a payment."""
    locked_payment = (
        Payment.objects.select_for_update(of=("self",))
        .select_related(
            "appointment",
            "appointment__customer",
            "appointment__provider",
            "appointment__provider__user",
            "appointment__offering",
            "organization",
            "payer",
        )
        .get(id=payment.id)
    )

    if locked_payment.payer_id != actor.id and not can_manage_payment(actor, locked_payment):
        raise PermissionDenied("You are not allowed to cancel this payment.")

    validate_payment_can_be_cancelled(payment=locked_payment)

    locked_payment.status = PaymentStatus.CANCELLED
    locked_payment.cancelled_at = timezone.now()
    locked_payment.save(update_fields=["status", "cancelled_at", "updated_at"])

    _create_payment_transaction(
        payment=locked_payment,
        transaction_type=PaymentTransactionType.CANCELLED,
        amount=locked_payment.amount,
        message="Payment cancelled.",
    )

    
    return locked_payment


@transaction.atomic
def refund_payment(
    *,
    payment,
    actor,
    refund_reason: str = "",
) -> Payment:
    """Refund a payment."""
    locked_payment = (
        Payment.objects.select_for_update(of=("self",))
        .select_related(
            "appointment",
            "appointment__customer",
            "appointment__provider",
            "appointment__provider__user",
            "appointment__offering",
            "organization",
            "payer",
        )
        .get(id=payment.id)
    )

    if not can_manage_payment(actor, locked_payment):
        raise PermissionDenied("You are not allowed to refund this payment.")

    validate_payment_can_be_refunded(payment=locked_payment)

    locked_payment.status = PaymentStatus.REFUNDED
    locked_payment.refunded_at = timezone.now()
    locked_payment.refund_reason = refund_reason.strip()
    locked_payment.save(
        update_fields=[
            "status",
            "refunded_at",
            "refund_reason",
            "updated_at",
        ]
    )

    _create_payment_transaction(
        payment=locked_payment,
        transaction_type=PaymentTransactionType.REFUNDED,
        amount=locked_payment.amount,
        message=locked_payment.refund_reason or "Payment refunded.",
    )

    publish_refund_success_notification(payment=locked_payment)

    
    return locked_payment
