import pytest

from apps.audit.enums import AuditAction, AuditObjectType, AuditStatus
from apps.audit.models import AuditLog
from apps.audit.services import create_audit_log
from apps.organizations.tests.factories import OrganizationFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_create_audit_log_creates_log():
    user = UserFactory()
    organization = OrganizationFactory(owner=user)

    create_audit_log(
        actor=user,
        organization=organization,
        action=AuditAction.APPOINTMENT_CREATED,
        status=AuditStatus.SUCCESS,
        target_object_type=AuditObjectType.APPOINTMENT,
        target_object_id="123",
        target_object_repr="Test appointment",
        metadata={"foo": "bar"},
        run_after_commit=False,
    )

    audit_log = AuditLog.objects.get()

    assert audit_log.actor == user
    assert audit_log.organization == organization
    assert audit_log.action == AuditAction.APPOINTMENT_CREATED
    assert audit_log.status == AuditStatus.SUCCESS
    assert audit_log.target_object_type == "appointment"
    assert audit_log.target_object_id == "123"
    assert audit_log.metadata["foo"] == "bar"
