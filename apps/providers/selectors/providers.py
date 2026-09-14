"""
Database selectors for ProviderProfile model.
"""

from django.db.models import QuerySet

from apps.providers.models import ProviderProfile


def get_active_providers() -> QuerySet[ProviderProfile]:
    """Return all active provider profiles from active organizations."""
    return (
        ProviderProfile.objects.filter(is_active=True, organization__is_active=True)
        .select_related("user", "organization", "branch")
        .order_by("-created_at")
    )


def get_provider_by_id(*, provider_id) -> ProviderProfile:
    """Return a provider profile by ID with related data prefetched."""
    return ProviderProfile.objects.select_related("user", "organization", "branch").get(
        id=provider_id
    )


def get_user_provider_profiles(*, user) -> QuerySet[ProviderProfile]:
    """Return all provider profiles belonging to a specific user."""
    return (
        ProviderProfile.objects.filter(user=user)
        .select_related("user", "organization", "branch")
        .order_by("-created_at")
    )


def get_organization_providers(
    *,
    organization,
    include_inactive: bool = False,
) -> QuerySet[ProviderProfile]:
    """Return providers for an organization, optionally including inactive ones."""
    queryset = (
        ProviderProfile.objects.filter(organization=organization)
        .select_related("user", "organization", "branch")
        .order_by("-created_at")
    )

    if not include_inactive:
        queryset = queryset.filter(is_active=True)

    return queryset
