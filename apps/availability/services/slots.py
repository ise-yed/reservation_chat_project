from datetime import datetime, timedelta

from django.core.cache import cache
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.appointments.selectors import get_provider_appointments_for_date
from apps.availability.selectors import (
    get_active_holiday_for_date,
    get_provider_time_offs_for_date,
    get_provider_working_hours_for_date,
)
from apps.availability.services.helpers import (
    get_offering_or_raise,
    get_provider_or_raise,
)

SLOTS_CACHE_TIMEOUT = 20 


def _slots_cache_key(*, provider_id, target_date) -> str:
    """The common key for all offerings of a provider on a given date."""
    return f"slots:{provider_id}:{target_date.isoformat()}"


def invalidate_provider_slots_cache(*, provider_id, target_date) -> None:
    """Invalidate the cache for available slots for a provider on a given date."""
    cache.delete(_slots_cache_key(provider_id=provider_id, target_date=target_date))


def _has_appointment_conflict(*, appointments, blocked_start_at, blocked_end_at) -> bool:
    """Check if there is an appointment conflict against a pre-fetched list."""
    for appointment in appointments:
        if (
            appointment.blocked_start_at < blocked_end_at
            and appointment.blocked_end_at > blocked_start_at
        ):
            return True
    return False


def _make_aware_datetime(*, target_date, target_time):
    """Make datetime timezone-aware."""
    current_timezone = timezone.get_current_timezone()
    value = datetime.combine(target_date, target_time)

    if timezone.is_naive(value):
        return timezone.make_aware(value, current_timezone)

    return value


def _has_time_off_conflict(*, time_offs, blocked_start_at, blocked_end_at) -> bool:
    """Check if there is a time off conflict."""
    for time_off in time_offs:
        if time_off.start_at < blocked_end_at and time_off.end_at > blocked_start_at:
            return True

    return False


def _compute_available_slots(*, provider, offering, target_date):
    """Compute the actual available slots — the same logic as before, just separated into a function."""
    holiday = get_active_holiday_for_date(
        organization=provider.organization,
        target_date=target_date,
    )
    if holiday:
        return []

    working_hours = get_provider_working_hours_for_date(
        provider=provider,
        target_date=target_date,
    )
    time_offs = list(
        get_provider_time_offs_for_date(
            provider=provider,
            target_date=target_date,
        )
    )
    appointments = list(
        get_provider_appointments_for_date(
            provider=provider,
            target_date=target_date,
        )
    )

    now = timezone.now()
    slots = []

    service_duration = timedelta(minutes=offering.duration_minutes)
    buffer_before = timedelta(minutes=offering.buffer_before_minutes)
    buffer_after = timedelta(minutes=offering.buffer_after_minutes)

    total_block_duration = buffer_before + service_duration + buffer_after

    if total_block_duration.total_seconds() <= 0:
        return []

    for working_hour in working_hours:
        working_start_at = _make_aware_datetime(
            target_date=target_date,
            target_time=working_hour.start_time,
        )
        working_end_at = _make_aware_datetime(
            target_date=target_date,
            target_time=working_hour.end_time,
        )

        current_start_at = working_start_at + buffer_before
        latest_start_at = working_end_at - service_duration - buffer_after

        while current_start_at <= latest_start_at:
            appointment_start_at = current_start_at
            appointment_end_at = appointment_start_at + service_duration

            blocked_start_at = appointment_start_at - buffer_before
            blocked_end_at = appointment_end_at + buffer_after

            is_future_slot = appointment_start_at > now
            has_time_off = _has_time_off_conflict(
                time_offs=time_offs,
                blocked_start_at=blocked_start_at,
                blocked_end_at=blocked_end_at,
            )
            has_appointment = _has_appointment_conflict(
                appointments=appointments,
                blocked_start_at=blocked_start_at,
                blocked_end_at=blocked_end_at,
            )

            if is_future_slot and not has_time_off and not has_appointment:
                slots.append(
                    {
                        "provider_id": str(provider.id),
                        "offering_id": str(offering.id),
                        "start_at": appointment_start_at,
                        "end_at": appointment_end_at,
                        "blocked_start_at": blocked_start_at,
                        "blocked_end_at": blocked_end_at,
                        "duration_minutes": offering.duration_minutes,
                        "price": offering.price,
                    }
                )

            current_start_at = current_start_at + total_block_duration

    return slots


def get_available_slots(
    *,
    provider_id,
    offering_id,
    target_date,
):
    """Get available time slots for a provider and offering on a specific date."""
    provider = get_provider_or_raise(provider_id=provider_id)
    offering = get_offering_or_raise(offering_id=offering_id)

    if offering.provider_id != provider.id:
        raise ValidationError({"offering_id": ["Offering does not belong to this provider."]})

    if not provider.is_active:
        return []
    if not provider.organization.is_active:
        return []
    if not offering.is_active:
        return []
    if not offering.organization.is_active:
        return []

    cache_key = _slots_cache_key(provider_id=provider.id, target_date=target_date)
    cached_by_offering = cache.get(cache_key)

    if cached_by_offering is None:
        cached_by_offering = {}

    offering_key = str(offering.id)

    if offering_key in cached_by_offering:
        return cached_by_offering[offering_key]

    slots = _compute_available_slots(
        provider=provider,
        offering=offering,
        target_date=target_date,
    )

    cached_by_offering[offering_key] = slots
    cache.set(cache_key, cached_by_offering, timeout=SLOTS_CACHE_TIMEOUT)

    return slots