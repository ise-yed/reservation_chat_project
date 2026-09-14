import logging

from django.db import transaction

from apps.audit.enums import AuditStatus
from apps.audit.models import AuditLog

logger = logging.getLogger(__name__)


def create_audit_log(
    *,
    actor=None,
    organization=None,
    action: str,
    status: str = AuditStatus.SUCCESS,
    target_object_type: str,
    target_object_id=None,
    target_object_repr: str = "",
    metadata: dict | None = None,
    error_message: str = "",
    ip_address=None,
    user_agent: str = "",
    run_after_commit: bool = True,
) -> None:
    """Create an audit log entry."""
    actor_id = getattr(actor, "id", None)
    organization_id = getattr(organization, "id", None)

    payload = {
        "actor_id": actor_id,
        "organization_id": organization_id,
        "action": action,
        "status": status,
        "target_object_type": target_object_type,
        "target_object_id": str(target_object_id) if target_object_id else "",
        "target_object_repr": target_object_repr[:255] if target_object_repr else "",
        "metadata": metadata or {},
        "error_message": error_message,
        "ip_address": ip_address,
        "user_agent": user_agent,
    }

    def _create() -> None:
        try:
            AuditLog.objects.create(**payload)
        except Exception:
            logger.exception("Could not create audit log.")

    if run_after_commit:
        transaction.on_commit(_create)
        return

    _create()
