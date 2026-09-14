from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.appointments.enums import (
    ACTIVE_APPOINTMENT_STATUSES,
    CANCELLABLE_APPOINTMENT_STATUSES,
    AppointmentStatus,
)
from apps.appointments.models import Appointment
from apps.offerings.models import Offering
from apps.providers.models import ProviderProfile


def validate_provider_and_offering(*, provider, offering) -> None:
    if offering.provider_id != provider.id:
        raise ValidationError({"offering_id": ["Offering does not belong to this provider."]})

    if offering.organization_id != provider.organization_id:
        raise ValidationError(
            {"offering_id": ["Offering organization does not match provider organization."]}
        )

    if not provider.is_active:
        raise ValidationError({"provider_id": ["Provider is not active."]})

    if not provider.organization.is_active:
        raise ValidationError({"provider_id": ["Provider organization is not active."]})

    if not offering.is_active:
        raise ValidationError({"offering_id": ["Offering is not active."]})

    if not offering.organization.is_active:
        raise ValidationError({"offering_id": ["Offering organization is not active."]})


def validate_appointment_start_at(*, start_at) -> None:
    if timezone.is_naive(start_at):
        raise ValidationError({"start_at": ["Appointment start datetime must be timezone-aware."]})

    if start_at <= timezone.now():
        raise ValidationError({"start_at": ["Appointment start time must be in the future."]})


def validate_no_appointment_conflict(
    *,
    provider,
    blocked_start_at,
    blocked_end_at,
    exclude_id=None,
) -> None:
    queryset = Appointment.objects.filter(
        provider=provider,
        status__in=ACTIVE_APPOINTMENT_STATUSES,
        blocked_start_at__lt=blocked_end_at,
        blocked_end_at__gt=blocked_start_at,
    )

    if exclude_id:
        queryset = queryset.exclude(id=exclude_id)

    if queryset.exists():
        raise ValidationError({"start_at": ["Selected time slot is already booked."]})


def validate_appointment_is_cancellable(*, appointment) -> None:
    if appointment.status not in CANCELLABLE_APPOINTMENT_STATUSES:
        raise ValidationError({"status": ["This appointment cannot be cancelled."]})


def validate_status_transition(*, appointment, new_status: str) -> None:
    current_status = appointment.status

    allowed_transitions = {
        AppointmentStatus.PENDING: [
            AppointmentStatus.CONFIRMED,
        ],
        AppointmentStatus.CONFIRMED: [
            AppointmentStatus.COMPLETED,
            AppointmentStatus.NO_SHOW,
        ],
        AppointmentStatus.CANCELLED_BY_CUSTOMER: [],
        AppointmentStatus.CANCELLED_BY_PROVIDER: [],
        AppointmentStatus.COMPLETED: [],
        AppointmentStatus.NO_SHOW: [],
    }

    if new_status not in AppointmentStatus.values:
        raise ValidationError({"status": ["Invalid appointment status."]})

    if new_status not in allowed_transitions[current_status]:
        raise ValidationError(
            {"status": [f"Cannot change appointment status from {current_status} to {new_status}."]}
        )


def get_provider_or_raise(*, provider_id) -> ProviderProfile:
    try:
        return ProviderProfile.objects.select_related("user", "organization", "branch").get(
            id=provider_id
        )
    except ProviderProfile.DoesNotExist as exc:
        raise ValidationError({"provider_id": ["Provider not found."]}) from exc


def get_offering_or_raise(*, offering_id) -> Offering:
    try:
        return Offering.objects.select_related(
            "organization",
            "provider",
            "provider__user",
            "provider__organization",
            "provider__branch",
        ).get(id=offering_id)
    except Offering.DoesNotExist as exc:
        raise ValidationError({"offering_id": ["Offering not found."]}) from exc
