from datetime import datetime, time

from django.db.models import QuerySet
from django.utils import timezone

from apps.availability.models import TimeOff


def get_active_time_offs() -> QuerySet[TimeOff]:
    """Get all active time offs."""
    return (
        TimeOff.objects.filter(
            is_active=True,
            provider__is_active=True,
            provider__organization__is_active=True,
        )
        .select_related(
            "provider",
            "provider__user",
            "provider__organization",
            "provider__branch",
        )
        .order_by("-start_at")
    )


def get_time_off_by_id(*, time_off_id) -> TimeOff:
    """Get time off by ID."""
    return TimeOff.objects.select_related(
        "provider",
        "provider__user",
        "provider__organization",
        "provider__branch",
    ).get(id=time_off_id)


def get_provider_time_offs(
    *,
    provider,
    include_inactive: bool = False,
) -> QuerySet[TimeOff]:
    """Get time offs for a specific provider."""
    queryset = (
        TimeOff.objects.filter(provider=provider)
        .select_related(
            "provider",
            "provider__user",
            "provider__organization",
            "provider__branch",
        )
        .order_by("-start_at")
    )

    if not include_inactive:
        queryset = queryset.filter(is_active=True)

    return queryset


def get_provider_time_offs_for_date(*, provider, target_date):
    """Get provider time offs for a specific date."""
    current_timezone = timezone.get_current_timezone()
    day_start = timezone.make_aware(
        datetime.combine(target_date, time.min),
        current_timezone,
    )
    day_end = timezone.make_aware(
        datetime.combine(target_date, time.max),
        current_timezone,
    )

    return TimeOff.objects.filter(
        provider=provider,
        is_active=True,
        start_at__lt=day_end,
        end_at__gt=day_start,
    ).order_by("start_at")
