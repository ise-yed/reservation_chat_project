from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.availability.models import WorkingHour
from apps.availability.permissions import can_manage_provider_availability
from apps.availability.services.helpers import (
    get_provider_or_raise,
    validate_no_overlapping_working_hour,
    validate_time_range,
    validate_weekday,
)


@transaction.atomic
def create_working_hour(
    *,
    actor,
    provider_id,
    weekday: int,
    start_time,
    end_time,
    is_active: bool = True,
) -> WorkingHour:
    """Create a new working hour."""
    provider = get_provider_or_raise(provider_id=provider_id)

    if not can_manage_provider_availability(actor, provider):
        raise PermissionDenied("You are not allowed to manage this provider availability.")

    if not provider.is_active:
        raise ValidationError(
            {"provider_id": ["Cannot create working hour for inactive provider."]}
        )

    if not provider.organization.is_active:
        raise ValidationError(
            {"provider_id": ["Cannot create working hour for provider in inactive organization."]}
        )

    validate_weekday(weekday)
    validate_time_range(start_time=start_time, end_time=end_time)

    if is_active:
        validate_no_overlapping_working_hour(
            provider=provider,
            weekday=weekday,
            start_time=start_time,
            end_time=end_time,
        )

    return WorkingHour.objects.create(
        provider=provider,
        weekday=weekday,
        start_time=start_time,
        end_time=end_time,
        is_active=is_active,
    )


@transaction.atomic
def update_working_hour(
    *,
    working_hour: WorkingHour,
    actor,
    **data,
) -> WorkingHour:
    """Update an existing working hour."""
    if not can_manage_provider_availability(actor, working_hour.provider):
        raise PermissionDenied("You are not allowed to manage this provider availability.")

    weekday = data.get("weekday", working_hour.weekday)
    start_time = data.get("start_time", working_hour.start_time)
    end_time = data.get("end_time", working_hour.end_time)
    is_active = data.get("is_active", working_hour.is_active)

    validate_weekday(weekday)
    validate_time_range(start_time=start_time, end_time=end_time)

    if is_active:
        validate_no_overlapping_working_hour(
            provider=working_hour.provider,
            weekday=weekday,
            start_time=start_time,
            end_time=end_time,
            exclude_id=working_hour.id,
        )

    allowed_fields = {
        "weekday",
        "start_time",
        "end_time",
        "is_active",
    }

    update_fields = []

    for field in allowed_fields:
        if field in data:
            setattr(working_hour, field, data[field])
            update_fields.append(field)

    if update_fields:
        update_fields.append("updated_at")
        working_hour.save(update_fields=update_fields)

    return working_hour
