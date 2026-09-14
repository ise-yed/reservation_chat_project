from django.db.models import QuerySet

from apps.availability.models import WorkingHour


def get_active_working_hours() -> QuerySet[WorkingHour]:
    """Get all active working hours."""
    return (
        WorkingHour.objects.filter(
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
        .order_by("weekday", "start_time")
    )


def get_working_hour_by_id(*, working_hour_id) -> WorkingHour:
    """Get working hour by ID."""
    return WorkingHour.objects.select_related(
        "provider",
        "provider__user",
        "provider__organization",
        "provider__branch",
    ).get(id=working_hour_id)


def get_provider_working_hours(
    *,
    provider,
    include_inactive: bool = False,
) -> QuerySet[WorkingHour]:
    """Get working hours for a specific provider."""
    queryset = (
        WorkingHour.objects.filter(provider=provider)
        .select_related(
            "provider",
            "provider__user",
            "provider__organization",
            "provider__branch",
        )
        .order_by("weekday", "start_time")
    )

    if not include_inactive:
        queryset = queryset.filter(is_active=True)

    return queryset


def get_provider_working_hours_for_date(*, provider, target_date):
    """Get provider working hours for a specific date."""
    return WorkingHour.objects.filter(
        provider=provider,
        weekday=target_date.weekday(),
        is_active=True,
    ).order_by("start_time")
