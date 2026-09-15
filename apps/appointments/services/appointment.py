from datetime import timedelta

from django.db import transaction
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
from apps.providers.models import ProviderProfile


def _calculate_appointment_times(*, offering, start_at):
    """Calculate appointment times based on offering and start time."""
    service_duration = timedelta(minutes=offering.duration_minutes)
    buffer_before = timedelta(minutes=offering.buffer_before_minutes)
    buffer_after = timedelta(minutes=offering.buffer_after_minutes)

    end_at = start_at + service_duration
    blocked_start_at = start_at - buffer_before
    blocked_end_at = end_at + buffer_after

    return end_at, blocked_start_at, blocked_end_at


def _validate_start_at_is_available_slot(*, provider, offering, start_at) -> None:
    """Validate that the start time is available."""
    target_date = timezone.localtime(start_at).date()

    slots = get_available_slots(
        provider_id=provider.id,
        offering_id=offering.id,
        target_date=target_date,
    )

    available_start_times = {slot["start_at"] for slot in slots}

    if start_at not in available_start_times:
        raise ValidationError({"start_at": ["Selected start time is not available."]})


@transaction.atomic
def create_appointment(
    *,
    customer,
    provider_id,
    offering_id,
    start_at,
    notes: str = "",
) -> Appointment:
    """Create a new appointment."""
    validate_appointment_start_at(start_at=start_at)

    provider = get_provider_or_raise(provider_id=provider_id)
    offering = get_offering_or_raise(offering_id=offering_id)

    validate_provider_and_offering(
        provider=provider,
        offering=offering,
    )

    _validate_start_at_is_available_slot(
        provider=provider,
        offering=offering,
        start_at=start_at,
    )

    locked_provider = (
        ProviderProfile.objects.select_for_update(of=("self",))
        .select_related("organization", "user")
        .get(id=provider.id)
    )
    validate_provider_and_offering(
        provider=locked_provider,
        offering=offering,
    )

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
        AppointmentStatus.PENDING if offering.requires_approval else AppointmentStatus.CONFIRMED
    )

    appointment = Appointment.objects.create(
        organization=locked_provider.organization,
        branch_id=locked_provider.branch_id,
        customer=customer,
        provider=locked_provider,
        offering=offering,
        start_at=start_at,
        end_at=end_at,
        blocked_start_at=blocked_start_at,
        blocked_end_at=blocked_end_at,
        status=initial_status,
        price=offering.price,
        notes=notes.strip(),
        created_by=customer,
    )

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
    """Cancel an appointment."""
    if not can_cancel_appointment(actor, appointment):
        raise PermissionDenied("You are not allowed to cancel this appointment.")

    if timezone.now() >= appointment.start_at:
        raise ValidationError("Cannot cancel an appointment that has already started.")

    validate_appointment_is_cancellable(appointment=appointment)

    old_status = appointment.status

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
    """Update appointment status."""
    if not can_manage_appointment(actor, appointment):
        raise PermissionDenied("You are not allowed to update this appointment status.")

    validate_status_transition(
        appointment=appointment,
        new_status=status,
    )

    old_status = appointment.status
    appointment.status = status
    appointment.save(update_fields=["status", "updated_at"])

    publish_appointment_status_notification(appointment=appointment)


    transaction.on_commit(
        lambda: invalidate_provider_slots_cache(
            provider_id=appointment.provider_id,
            target_date=timezone.localtime(appointment.start_at).date(),
        )
    )
    return appointment
