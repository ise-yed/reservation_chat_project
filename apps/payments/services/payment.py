from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.appointments.enums import AppointmentStatus
from apps.appointments.models import Appointment
from apps.appointments.services import confirm_paid_appointment
from apps.payments.enums import PaymentMethod, PaymentStatus
from apps.payments.gateway import get_gateway
from apps.payments.models import Payment
from apps.payments.permissions import can_manage_payment


def build_callback_url(request, payment_id) -> str:
    return request.build_absolute_uri(reverse("payments:callback", kwargs={"pk": payment_id}))


def _lock_appointment_and_payment(payment_id):
    """
    Always lock the appointment first, then the payment
    (same order as the expiry task) to avoid deadlocks.
    """
    try:
        appointment = (
            Appointment.objects.select_for_update(of=("self",))
            .select_related("organization", "branch", "customer", "provider__user", "offering")
            .get(payment__id=payment_id)
        )
    except Appointment.DoesNotExist as exc:
        raise Payment.DoesNotExist from exc
    payment = Payment.objects.select_for_update().get(id=payment_id)
    payment.appointment = appointment
    return appointment, payment


@transaction.atomic
def start_online_payment(*, payment_id, actor, callback_url: str):
    """Create (or retry) a gateway payment. Returns (payment, pay_url)."""
    appointment, payment = _lock_appointment_and_payment(payment_id)

    if appointment.customer_id != actor.id:
        raise PermissionDenied("You are not allowed to pay for this appointment.")
    if payment.method != PaymentMethod.ONLINE:
        raise ValidationError("This payment is not an online payment.")
    if payment.status not in (PaymentStatus.PENDING, PaymentStatus.FAILED):
        raise ValidationError("This payment can no longer be started.")
    if appointment.status != AppointmentStatus.PENDING:
        raise ValidationError("This appointment is no longer waiting for payment.")

    minutes = getattr(settings, "PAYMENT_EXPIRE_MINUTES", 15)
    if appointment.created_at < timezone.now() - timedelta(minutes=minutes):
        raise ValidationError("The payment window has expired. Please book again.")

    authority, pay_url = get_gateway().start(payment=payment, callback_url=callback_url)
    payment.gateway_reference = authority
    payment.status = PaymentStatus.PENDING
    payment.save(update_fields=["gateway_reference", "status", "updated_at"])
    return payment, pay_url


@transaction.atomic
def verify_online_payment(*, payment_id, params: dict) -> Payment:
    """Gateway callback. Verifies the payment and confirms the appointment."""
    appointment, payment = _lock_appointment_and_payment(payment_id)

    if payment.status == PaymentStatus.PAID:  # idempotent
        return payment
    if payment.method != PaymentMethod.ONLINE or payment.status != PaymentStatus.PENDING:
        raise ValidationError("This payment is not waiting for verification.")

    reference = None
    # If the appointment expired/cancelled meanwhile we must not verify (gateways auto-reverse
    # unverified payments), so the customer is not charged for a slot that is gone.
    if appointment.status == AppointmentStatus.PENDING:
        reference = get_gateway().verify(payment=payment, params=params)

    if reference:
        payment.status = PaymentStatus.PAID
        payment.paid_at = timezone.now()
        payment.gateway_reference = reference
        payment.save(update_fields=["status", "paid_at", "gateway_reference", "updated_at"])
        confirm_paid_appointment(appointment=appointment)
    else:
        payment.status = PaymentStatus.FAILED
        payment.save(update_fields=["status", "updated_at"])
    return payment


@transaction.atomic
def mark_paid_in_person(*, payment_id, actor) -> Payment:
    """Provider/staff confirms that the patient paid at the clinic."""
    appointment, payment = _lock_appointment_and_payment(payment_id)

    if not can_manage_payment(actor, payment):
        raise PermissionDenied("You are not allowed to update this payment.")
    if payment.method != PaymentMethod.IN_PERSON:
        raise ValidationError("Only in-person payments can be marked as paid manually.")
    if payment.status != PaymentStatus.PENDING:
        raise ValidationError("This payment is not pending.")
    if appointment.status not in (AppointmentStatus.CONFIRMED, AppointmentStatus.COMPLETED):
        raise ValidationError("The appointment must be confirmed first.")

    payment.status = PaymentStatus.PAID
    payment.paid_at = timezone.now()
    payment.save(update_fields=["status", "paid_at", "updated_at"])
    return payment
