from django.db.models import QuerySet

from apps.offerings.models import Offering


def get_active_offerings() -> QuerySet[Offering]:
    """Get all active offerings."""
    return (
        Offering.objects.filter(
            is_active=True,
            organization__is_active=True,
            provider__is_active=True,
        )
        .select_related(
            "organization",
            "provider",
            "provider__user",
            "provider__branch",
            "category",
        )
        .order_by("-created_at")
    )


def get_offering_by_id(*, offering_id) -> Offering:
    """Get an offering by ID."""
    return Offering.objects.select_related(
        "organization",
        "provider",
        "provider__user",
        "provider__branch",
        "category",
    ).get(id=offering_id)


def get_organization_offerings(
    *,
    organization,
    include_inactive: bool = False,
) -> QuerySet[Offering]:
    """Get offerings for an organization."""
    queryset = (
        Offering.objects.filter(organization=organization)
        .select_related(
            "organization",
            "provider",
            "provider__user",
            "provider__branch",
            "category",
        )
        .order_by("-created_at")
    )

    if not include_inactive:
        queryset = queryset.filter(
            is_active=True,
            provider__is_active=True,
        )

    return queryset


def get_provider_offerings(
    *,
    provider,
    include_inactive: bool = False,
) -> QuerySet[Offering]:
    """Get offerings for a provider."""
    queryset = (
        Offering.objects.filter(provider=provider)
        .select_related(
            "organization",
            "provider",
            "provider__user",
            "provider__branch",
            "category",
        )
        .order_by("-created_at")
    )

    if not include_inactive:
        queryset = queryset.filter(is_active=True)

    return queryset


def get_user_offerings(*, user) -> QuerySet[Offering]:
    """Get offerings for a user."""
    return (
        Offering.objects.filter(provider__user=user)
        .select_related(
            "organization",
            "provider",
            "provider__user",
            "provider__branch",
            "category",
        )
        .order_by("-created_at")
    )
