from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.organizations.permissions import can_manage_organization


def can_manage_offering(user, offering) -> bool:
    """Check if user can manage an offering."""
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return can_manage_organization(user, offering.organization)


def can_view_inactive_offering(user, offering) -> bool:
    """Check if user can view an inactive offering."""
    if not user or not user.is_authenticated:
        return False

    if can_manage_offering(user, offering):
        return True

    return offering.provider.user_id == user.id


class IsOfferingManagerOrReadOnly(BasePermission):
    """Allow read-only access to all users, write access only for managers."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return can_manage_offering(request.user, obj)
