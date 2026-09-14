from django.db.models import Q, QuerySet

from apps.audit.models import AuditLog


def audit_log_queryset() -> QuerySet[AuditLog]:
    """Get base audit log queryset with related data."""
    return AuditLog.objects.select_related(
        "actor",
        "organization",
    ).order_by("-created_at")


def get_audit_log_by_id(*, audit_log_id) -> AuditLog:
    """Get a single audit log by ID."""
    return audit_log_queryset().get(id=audit_log_id)


def get_visible_audit_logs_for_user(*, user) -> QuerySet[AuditLog]:
    """Get audit logs visible to a user."""
    queryset = audit_log_queryset()

    if user.is_superuser:
        return queryset

    return queryset.filter(Q(actor=user) | Q(organization__owner=user)).distinct()


def get_user_audit_logs(*, user) -> QuerySet[AuditLog]:
    """Get audit logs for a specific user."""
    return audit_log_queryset().filter(actor=user)


def get_organization_audit_logs(*, organization) -> QuerySet[AuditLog]:
    """Get audit logs for a specific organization."""
    return audit_log_queryset().filter(organization=organization)
