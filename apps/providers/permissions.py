"""
Permission classes and helper functions for ProviderProfile access control.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.organizations.permissions import can_manage_organization


def can_manage_provider_profile(user, provider_profile) -> bool:
    """Check if user can manage a provider profile (owner, org admin, or superuser)."""
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if provider_profile.user_id == user.id:
        return True

    return can_manage_organization(user, provider_profile.organization)


def can_create_provider_profile(user, organization) -> bool:
    """Check if user can create a provider profile in an organization."""
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return can_manage_organization(user, organization)


def can_manage_provider_organization_fields(user, provider_profile) -> bool:
    """Check if user can update organization-level fields (branch, is_active)."""
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return can_manage_organization(user, provider_profile.organization)


class IsProviderProfileManagerOrReadOnly(BasePermission):
    """Allow read access to everyone, write access only to authorized users."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return can_manage_provider_profile(request.user, obj)
