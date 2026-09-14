from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.organizations.permissions import can_manage_organization


def can_manage_provider_availability(user, provider) -> bool:
    """Check if user can manage provider availability."""
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if provider.user_id == user.id:
        return True

    return can_manage_organization(user, provider.organization)


def can_manage_holiday(user, holiday) -> bool:
    """Check if user can manage holiday."""
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return can_manage_organization(user, holiday.organization)


def can_manage_organization_holidays(user, organization) -> bool:
    """Check if user can manage organization holidays."""
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return can_manage_organization(user, organization)


class IsWorkingHourManagerOrReadOnly(BasePermission):
    """Allow read-only to all, write only for managers."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return can_manage_provider_availability(request.user, obj.provider)


class IsTimeOffManagerOrReadOnly(BasePermission):
    """Allow read-only to all, write only for managers."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return can_manage_provider_availability(request.user, obj.provider)


class IsHolidayManagerOrReadOnly(BasePermission):
    """Allow read-only to all, write only for managers."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return can_manage_holiday(request.user, obj)
