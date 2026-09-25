"""
Shared permission classes used across multiple apps.

Role hierarchy:
  super_admin  — sees everything, can do everything
  org_admin    — scoped to their own organization(s)
  staff        — scoped to their org, read-only on config, full on appointments/payments
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.users.enums import UserRoles

ADMIN_ROLES = {UserRoles.STAFF, UserRoles.ORG_ADMIN, UserRoles.SUPER_ADMIN}


# ── helpers ──────────────────────────────────────────────────────────────────

def is_super_admin(user) -> bool:
    return bool(user and user.is_authenticated and (user.is_superuser or user.role == UserRoles.SUPER_ADMIN))


def is_org_admin(user) -> bool:
    return bool(user and user.is_authenticated and user.role == UserRoles.ORG_ADMIN)


def is_staff_role(user) -> bool:
    return bool(user and user.is_authenticated and user.role == UserRoles.STAFF)


def is_any_admin(user) -> bool:
    return bool(user and user.is_authenticated and (user.is_superuser or user.role in ADMIN_ROLES))


def get_user_org_ids(user):
    """
    Returns the set of organization UUIDs the user owns/admins.
    super_admin -> None  (means 'all — unrestricted')
    org_admin/staff -> UUIDs of their owned organizations
    """
    if is_super_admin(user):
        return None
    return set(user.owned_organizations.values_list("id", flat=True))


# ── permission classes ────────────────────────────────────────────────────────

class IsAdminUser(BasePermission):
    """
    Allows access to staff / org_admin / super_admin / Django superusers.
    Scope enforcement is done inside each view's get_queryset().
    """
    message = "You must be an admin to perform this action."

    def has_permission(self, request, view):
        return is_any_admin(request.user)


class IsSuperAdminUser(BasePermission):
    """Allows access only to super_admin / Django superusers."""
    message = "You must be a super admin to perform this action."

    def has_permission(self, request, view):
        return is_super_admin(request.user)


class IsSuperAdminOrReadOnly(BasePermission):
    """
    SAFE methods (GET) -> any admin;
    write methods (POST/PATCH/DELETE) -> super_admin only.
    Used for Category CRUD.
    """
    message = "Only super admins can modify this resource."

    def has_permission(self, request, view):
        if not is_any_admin(request.user):
            return False
        if request.method in SAFE_METHODS:
            return True
        return is_super_admin(request.user)


class IsOrgAdminOrSuperAdmin(BasePermission):
    """org_admin and super_admin — for org/branch/provider/offering management."""
    message = "You must be an organization admin or super admin."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return is_super_admin(request.user) or is_org_admin(request.user)
