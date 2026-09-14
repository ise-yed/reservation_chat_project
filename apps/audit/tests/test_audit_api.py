import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.enums import AuditAction
from apps.audit.models import AuditLog
from apps.organizations.tests.factories import OrganizationFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def get_client(user=None):
    client = APIClient()
    if user:
        client.force_authenticate(user=user)
    return client


def test_user_can_list_own_audit_logs():
    user = UserFactory()
    organization = OrganizationFactory(owner=user)

    AuditLog.objects.create(
        actor=user,
        organization=organization,
        action=AuditAction.APPOINTMENT_CREATED,
        target_object_type="appointment",
        target_object_id="123",
        target_object_repr="Test appointment",
    )

    client = get_client(user)
    url = reverse("audit:my-list")

    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["results"][0]["action"] == AuditAction.APPOINTMENT_CREATED


def test_organization_owner_can_list_organization_audit_logs():
    owner = UserFactory()
    organization = OrganizationFactory(owner=owner)

    AuditLog.objects.create(
        actor=owner,
        organization=organization,
        action=AuditAction.PAYMENT_INITIATED,
        target_object_type="payment",
        target_object_id="456",
        target_object_repr="Test payment",
    )

    client = get_client(owner)
    url = reverse(
        "audit:organization-list",
        kwargs={"organization_id": organization.id},
    )

    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1


def test_non_owner_cannot_list_organization_audit_logs():
    owner = UserFactory()
    other_user = UserFactory()
    organization = OrganizationFactory(owner=owner)

    AuditLog.objects.create(
        actor=owner,
        organization=organization,
        action=AuditAction.PAYMENT_INITIATED,
        target_object_type="payment",
        target_object_id="456",
    )

    client = get_client(other_user)
    url = reverse(
        "audit:organization-list",
        kwargs={"organization_id": organization.id},
    )

    response = client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
