"""
Permission classes and helper functions for organization access control.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.users.enums import UserRoles


def can_create_organization(user) -> bool:
    """Check if user has permission to create an organization."""
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return user.role in {
        UserRoles.PROVIDER,
        UserRoles.ORG_ADMIN,
        UserRoles.SUPER_ADMIN,
    }


def can_manage_organization(user, organization) -> bool:
    """Check if user can manage (edit/delete) a specific organization."""
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return organization.owner_id == user.id


class CanCreateOrganizationOrReadOnly(BasePermission):
    """
    Allow read access to all authenticated users, but create only for authorized roles.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated

        return can_create_organization(request.user)


class IsOrganizationOwnerOrReadOnly(BasePermission):
    """
    Allow read access to everyone, but write access only to organization owner.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return can_manage_organization(request.user, obj)


class IsBranchOrganizationOwnerOrReadOnly(BasePermission):
    """
    Allow read access to everyone, but write access only to the branch's organization owner.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return can_manage_organization(request.user, obj.organization)
