from decimal import Decimal

from rest_framework.exceptions import ValidationError

from apps.appointments.choices import AppointmentStatus
from apps.payments.choices import PaymentStatus

PAYABLE_APPOINTMENT_STATUSES = [
    AppointmentStatus.PENDING,
    AppointmentStatus.CONFIRMED,
]


def validate_appointment_is_payable(*, appointment) -> None:
    """Validate that an appointment is payable."""
    if appointment.status not in PAYABLE_APPOINTMENT_STATUSES:
        raise ValidationError({"appointment_id": ["This appointment is not payable."]})

    if appointment.price is None:
        raise ValidationError({"appointment_id": ["Appointment has no payable price."]})

    if Decimal(appointment.price) < 0:
        raise ValidationError({"appointment_id": ["Appointment price is invalid."]})


def validate_payment_can_be_paid(*, payment) -> None:
    """Validate that a payment can be marked as paid."""
    if payment.status != PaymentStatus.PENDING:
        raise ValidationError({"status": ["Only pending payments can be marked as paid."]})


def validate_payment_can_fail(*, payment) -> None:
    """Validate that a payment can be marked as failed."""
    if payment.status != PaymentStatus.PENDING:
        raise ValidationError({"status": ["Only pending payments can be marked as failed."]})


def validate_payment_can_be_cancelled(*, payment) -> None:
    """Validate that a payment can be cancelled."""
    if payment.status != PaymentStatus.PENDING:
        raise ValidationError({"status": ["Only pending payments can be cancelled."]})


def validate_payment_can_be_refunded(*, payment) -> None:
    """Validate that a payment can be refunded."""
    if payment.status != PaymentStatus.PAID:
        raise ValidationError({"status": ["Only paid payments can be refunded."]})
