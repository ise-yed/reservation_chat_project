from apps.organizations.permissions import can_manage_organization


def can_view_audit_log(user, audit_log) -> bool:
    """Check if user can view an audit log."""
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if audit_log.actor_id == user.id:
        return True

    if audit_log.organization_id:
        return can_manage_organization(user, audit_log.organization)

    return False


def can_view_organization_audit_logs(user, organization) -> bool:
    """Check if user can view organization audit logs."""
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return can_manage_organization(user, organization)
