from django.db.models import QuerySet

from apps.availability.models import Holiday


def get_active_holidays() -> QuerySet[Holiday]:
    """Get all active holidays."""
    return (
        Holiday.objects.filter(
            is_active=True,
            organization__is_active=True,
        )
        .select_related("organization")
        .order_by("-date")
    )


def get_holiday_by_id(*, holiday_id) -> Holiday:
    """Get holiday by ID."""
    return Holiday.objects.select_related("organization").get(id=holiday_id)


def get_organization_holidays(
    *,
    organization,
    include_inactive: bool = False,
) -> QuerySet[Holiday]:
    """Get holidays for a specific organization."""
    queryset = (
        Holiday.objects.filter(organization=organization)
        .select_related("organization")
        .order_by("-date")
    )

    if not include_inactive:
        queryset = queryset.filter(is_active=True)

    return queryset


def get_active_holiday_for_date(*, organization, target_date):
    """Get active holiday for a specific date."""
    return Holiday.objects.filter(
        organization=organization,
        date=target_date,
        is_active=True,
    ).first()
