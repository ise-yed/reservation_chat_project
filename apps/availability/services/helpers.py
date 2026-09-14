from rest_framework.exceptions import ValidationError

from apps.availability.models import WorkingHour
from apps.offerings.models import Offering
from apps.organizations.models import Organization
from apps.providers.models import ProviderProfile


def get_provider_or_raise(*, provider_id) -> ProviderProfile:
    """Get provider by ID or raise validation error."""
    try:
        return ProviderProfile.objects.select_related("user", "organization", "branch").get(
            id=provider_id
        )
    except ProviderProfile.DoesNotExist as exc:
        raise ValidationError({"provider_id": ["Provider not found."]}) from exc


def get_organization_or_raise(*, organization_id) -> Organization:
    """Get organization by ID or raise validation error."""
    try:
        return Organization.objects.get(id=organization_id)
    except Organization.DoesNotExist as exc:
        raise ValidationError({"organization_id": ["Organization not found."]}) from exc


def get_offering_or_raise(*, offering_id) -> Offering:
    """Get offering by ID or raise validation error."""
    try:
        return Offering.objects.select_related(
            "organization",
            "provider",
            "provider__user",
            "provider__organization",
        ).get(id=offering_id)
    except Offering.DoesNotExist as exc:
        raise ValidationError({"offering_id": ["Offering not found."]}) from exc


def validate_weekday(value: int) -> None:
    """Validate weekday is between 0 and 6."""
    if value < 0 or value > 6:
        raise ValidationError({"weekday": ["Weekday must be between 0 and 6."]})


def validate_time_range(*, start_time, end_time) -> None:
    """Validate that end time is after start time."""
    if end_time <= start_time:
        raise ValidationError({"end_time": ["End time must be after start time."]})


def validate_datetime_range(*, start_at, end_at) -> None:
    """Validate that end datetime is after start datetime."""
    if end_at <= start_at:
        raise ValidationError({"end_at": ["End datetime must be after start datetime."]})


def validate_no_overlapping_working_hour(
    *,
    provider,
    weekday,
    start_time,
    end_time,
    exclude_id=None,
) -> None:
    """Validate no overlapping working hour exists."""
    queryset = WorkingHour.objects.filter(
        provider=provider,
        weekday=weekday,
        is_active=True,
        start_time__lt=end_time,
        end_time__gt=start_time,
    )

    if exclude_id:
        queryset = queryset.exclude(id=exclude_id)

    if queryset.exists():
        raise ValidationError(
            {"start_time": ["This working hour overlaps with another active working hour."]}
        )
