from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.appointments.enums import AppointmentStatus
from apps.appointments.models import Appointment
from apps.appointments.permissions import (
    can_cancel_appointment,
    can_manage_appointment,
)
from apps.appointments.services.helpers import (
    get_offering_or_raise,
    get_provider_or_raise,
    validate_appointment_is_cancellable,
    validate_appointment_start_at,
    validate_no_appointment_conflict,
    validate_provider_and_offering,
    validate_status_transition,
)
from apps.appointments.services.notification import (
    publish_appointment_cancelled_notification,
    publish_appointment_created_notification,
    publish_appointment_status_notification,
)
from apps.availability.services import get_available_slots, invalidate_provider_slots_cache
from apps.chat.models import Conversation
from apps.offerings.enums import VisitMode
from apps.payments.enums import PaymentMethod, PaymentStatus
from apps.payments.models import Payment
from apps.providers.models import ProviderProfile


def _calculate_appointment_times(*, offering, start_at):
    service_duration = timedelta(minutes=offering.duration_minutes)
    buffer_before = timedelta(minutes=offering.buffer_before_minutes)
    buffer_after = timedelta(minutes=offering.buffer_after_minutes)


    end_at = start_at + service_duration
    blocked_start_at = start_at - buffer_before
    blocked_end_at = end_at + buffer_after


    return end_at, blocked_start_at, blocked_end_at



def _validate_start_at_is_available_slot(*, provider, offering, start_at) -> None:
    target_date = timezone.localtime(start_at).date()
    slots = get_available_slots(
        provider_id=provider.id,
        offering_id=offering.id,
        target_date=target_date,
    )
    available_start_times = {slot["start_at"] for slot in slots}


    if start_at not in available_start_times:
        raise ValidationError({"start_at": ["Selected start time is not available."]})



def _validate_payment_method(*, offering, payment_method) -> None:
    """Online visits must be paid online; in-person visits may be paid online or at the clinic."""
    if offering.visit_mode == VisitMode.ONLINE_CHAT and payment_method != PaymentMethod.ONLINE:
        raise ValidationError(
            {"payment_method": ["Online visits can only be paid online."]}
        )


def _get_or_create_conversation_safe(customer, provider_user):
    """Safely get or create conversation handling Race Conditions according to V4 spec."""
    try:
        # استفاده از atomic داخلی تا در صورت IntegrityError کل ساخت نوبت متوقف نشود
        with transaction.atomic():
            conversation, _ = Conversation.objects.get_or_create(
                customer=customer,
                provider=provider_user,
            )
            return conversation
    except IntegrityError:
        return Conversation.objects.get(
            customer=customer,
            provider=provider_user,
        )



@transaction.atomic
def create_appointment(
    *,
    customer,
    provider_id,
    offering_id,
    start_at,
    notes: str = "",
    payment_method: str | None = None,
) -> Appointment:
    validate_appointment_start_at(start_at=start_at)


    provider = get_provider_or_raise(provider_id=provider_id)
    offering = get_offering_or_raise(offering_id=offering_id)


    validate_provider_and_offering(provider=provider, offering=offering)
    _validate_start_at_is_available_slot(provider=provider, offering=offering, start_at=start_at)

    # payment_method=None -> no payment handling (internal/legacy callers). The API always sends one.
    payment_required = payment_method is not None and offering.price > 0
    if payment_required:
        _validate_payment_method(offering=offering, payment_method=payment_method)
    # Online payment is taken at booking time: the slot is held (PENDING) until it is paid.
    awaiting_online_payment = payment_required and payment_method == PaymentMethod.ONLINE


    locked_provider = (
        ProviderProfile.objects.select_for_update(of=("self",))
        .select_related("organization", "user")
        .get(id=provider.id)
    )
    validate_provider_and_offering(provider=locked_provider, offering=offering)


    end_at, blocked_start_at, blocked_end_at = _calculate_appointment_times(
        offering=offering,
        start_at=start_at,
    )


    validate_no_appointment_conflict(
        provider=locked_provider,
        blocked_start_at=blocked_start_at,
        blocked_end_at=blocked_end_at,
    )


    initial_status = (
        AppointmentStatus.PENDING
        if (awaiting_online_payment or offering.requires_approval)
        else AppointmentStatus.CONFIRMED
    )


    conversation = None
    # ایجاد چت منحصراً برای نوبت‌های "آنلاین" و "تأییدشده"
    if offering.visit_mode == VisitMode.ONLINE_CHAT and initial_status == AppointmentStatus.CONFIRMED:
        conversation = _get_or_create_conversation_safe(customer, locked_provider.user)


    appointment = Appointment.objects.create(
        organization=locked_provider.organization,
        branch_id=locked_provider.branch_id,
        customer=customer,
        provider=locked_provider,
        offering=offering,
        conversation=conversation,
        visit_mode=offering.visit_mode,
        start_at=start_at,
        end_at=end_at,
        blocked_start_at=blocked_start_at,
        blocked_end_at=blocked_end_at,
        status=initial_status,
        price=offering.price,
        notes=notes.strip(),
        created_by=customer,
    )


    if payment_required:
        Payment.objects.create(
            appointment=appointment,
            amount=appointment.price,
            method=payment_method,
        )

    # For online payment the notification is sent after the payment succeeds.
    if not awaiting_online_payment:
        publish_appointment_created_notification(appointment=appointment)


    transaction.on_commit(
        lambda: invalidate_provider_slots_cache(
            provider_id=locked_provider.id,
            target_date=timezone.localtime(appointment.start_at).date(),
        )
    )


    return appointment



@transaction.atomic
def cancel_appointment(
    *,
    appointment: Appointment,
    actor,
    cancel_reason: str = "",
) -> Appointment:
    if not can_cancel_appointment(actor, appointment):
        raise PermissionDenied("You are not allowed to cancel this appointment.")


    if timezone.now() >= appointment.start_at:
        raise ValidationError("Cannot cancel an appointment that has already started.")


    validate_appointment_is_cancellable(appointment=appointment)


    if appointment.customer_id == actor.id:
        appointment.status = AppointmentStatus.CANCELLED_BY_CUSTOMER
    else:
        appointment.status = AppointmentStatus.CANCELLED_BY_PROVIDER


    appointment.cancelled_by = actor
    appointment.cancelled_at = timezone.now()
    appointment.cancel_reason = cancel_reason.strip()


    appointment.save(
        update_fields=[
            "status",
            "cancelled_by",
            "cancelled_at",
            "cancel_reason",
            "updated_at",
        ]
    )


    payment = getattr(appointment, "payment", None)
    if payment and payment.status == PaymentStatus.PENDING:
        payment.status = PaymentStatus.CANCELLED
        payment.save(update_fields=["status", "updated_at"])
    # A PAID payment stays PAID: staff refunds it manually and marks it REFUNDED in admin.

    publish_appointment_cancelled_notification(appointment=appointment)


    transaction.on_commit(
        lambda: invalidate_provider_slots_cache(
            provider_id=appointment.provider_id,
            target_date=timezone.localtime(appointment.start_at).date(),
        )
    )


    return appointment



@transaction.atomic
def update_appointment_status(
    *,
    appointment: Appointment,
    actor,
    status: str,
) -> Appointment:
    if not can_manage_appointment(actor, appointment):
        raise PermissionDenied("You are not allowed to update this appointment status.")


    validate_status_transition(appointment=appointment, new_status=status)

    if status == AppointmentStatus.CONFIRMED:
        payment = getattr(appointment, "payment", None)
        if payment and payment.method == PaymentMethod.ONLINE and payment.status != PaymentStatus.PAID:
            raise ValidationError({"status": ["Online payment has not been completed."]})


    old_status = appointment.status
    appointment.status = status
    update_fields = ["status", "updated_at"]


    # ثبت زمان پایان (تکمیل) نوبت
    if status == AppointmentStatus.COMPLETED and old_status != AppointmentStatus.COMPLETED:
        appointment.completed_at = timezone.now()
        update_fields.append("completed_at")


    # اتصال به چت فقط در صورت تغییر وضعیت از PENDING به CONFIRMED برای ویزیت‌های آنلاین
    if status == AppointmentStatus.CONFIRMED and appointment.visit_mode == VisitMode.ONLINE_CHAT and appointment.conversation_id is None:
        conversation = _get_or_create_conversation_safe(appointment.customer, appointment.provider.user)
        appointment.conversation = conversation
        update_fields.append("conversation")


    appointment.save(update_fields=update_fields)
    publish_appointment_status_notification(appointment=appointment)


    transaction.on_commit(
        lambda: invalidate_provider_slots_cache(
            provider_id=appointment.provider_id,
            target_date=timezone.localtime(appointment.start_at).date(),
        )
    )
    return appointment




def confirm_paid_appointment(*, appointment: Appointment) -> Appointment:
    """
    Called by the payments app after a verified online payment.
    The caller must already hold the appointment row lock (select_for_update).
    """
    if appointment.status != AppointmentStatus.PENDING:
        return appointment

    # Offerings that require approval stay PENDING until the provider confirms.
    if not appointment.offering.requires_approval:
        appointment.status = AppointmentStatus.CONFIRMED
        update_fields = ["status", "updated_at"]
        if appointment.visit_mode == VisitMode.ONLINE_CHAT and appointment.conversation_id is None:
            appointment.conversation = _get_or_create_conversation_safe(
                appointment.customer, appointment.provider.user
            )
            update_fields.append("conversation")
        appointment.save(update_fields=update_fields)

    publish_appointment_created_notification(appointment=appointment)
    return appointment


@transaction.atomic
def _expire_unpaid_appointment(appointment_id) -> bool:
    appointment = (
        Appointment.objects.select_for_update(of=("self",))
        .select_related("payment")
        .get(id=appointment_id)
    )
    payment = getattr(appointment, "payment", None)
    if (
        appointment.status != AppointmentStatus.PENDING
        or payment is None
        or payment.status not in (PaymentStatus.PENDING, PaymentStatus.FAILED)
    ):
        return False

    now = timezone.now()
    appointment.status = AppointmentStatus.CANCELLED_BY_CUSTOMER
    appointment.cancelled_at = now
    appointment.cancel_reason = "Online payment was not completed in time."
    appointment.save(update_fields=["status", "cancelled_at", "cancel_reason", "updated_at"])

    payment.status = PaymentStatus.CANCELLED
    payment.save(update_fields=["status", "updated_at"])

    transaction.on_commit(
        lambda: invalidate_provider_slots_cache(
            provider_id=appointment.provider_id,
            target_date=timezone.localtime(appointment.start_at).date(),
        )
    )
    return True


def expire_unpaid_appointments() -> int:
    """Release slots of appointments whose online payment was not completed in time."""
    minutes = getattr(settings, "PAYMENT_EXPIRE_MINUTES", 15)
    cutoff = timezone.now() - timedelta(minutes=minutes)
    ids = list(
        Appointment.objects.filter(
            status=AppointmentStatus.PENDING,
            payment__method=PaymentMethod.ONLINE,
            payment__status__in=[PaymentStatus.PENDING, PaymentStatus.FAILED],
            created_at__lt=cutoff,
        ).values_list("id", flat=True)
    )
    return sum(1 for appointment_id in ids if _expire_unpaid_appointment(appointment_id))
