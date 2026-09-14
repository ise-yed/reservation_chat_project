from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.availability.models import TimeOff
from apps.availability.permissions import can_manage_provider_availability
from apps.availability.services.helpers import get_provider_or_raise, validate_datetime_range


@transaction.atomic
def create_time_off(
    *,
    actor,
    provider_id,
    start_at,
    end_at,
    reason: str = "",
    is_active: bool = True,
) -> TimeOff:
    """Create a new time off."""
    provider = get_provider_or_raise(provider_id=provider_id)

    if not can_manage_provider_availability(actor, provider):
        raise PermissionDenied("You are not allowed to manage this provider availability.")

    if not provider.is_active:
        raise ValidationError({"provider_id": ["Cannot create time off for inactive provider."]})

    validate_datetime_range(start_at=start_at, end_at=end_at)

    return TimeOff.objects.create(
        provider=provider,
        start_at=start_at,
        end_at=end_at,
        reason=reason.strip(),
        is_active=is_active,
    )


@transaction.atomic
def update_time_off(
    *,
    time_off: TimeOff,
    actor,
    **data,
) -> TimeOff:
    """Update an existing time off."""
    if not can_manage_provider_availability(actor, time_off.provider):
        raise PermissionDenied("You are not allowed to manage this provider availability.")

    start_at = data.get("start_at", time_off.start_at)
    end_at = data.get("end_at", time_off.end_at)

    validate_datetime_range(start_at=start_at, end_at=end_at)

    allowed_fields = {
        "start_at",
        "end_at",
        "reason",
        "is_active",
    }

    update_fields = []

    for field in allowed_fields:
        if field in data:
            value = data[field]
            if isinstance(value, str):
                value = value.strip()

            setattr(time_off, field, value)
            update_fields.append(field)

    if update_fields:
        update_fields.append("updated_at")
        time_off.save(update_fields=update_fields)

    return time_off
