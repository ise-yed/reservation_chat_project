"""
Tests for organization service layer operations.
"""

import pytest
from rest_framework.exceptions import PermissionDenied

from apps.organizations.services import create_organization, update_organization
from apps.organizations.tests.factories import OrganizationFactory
from apps.users.enums import UserRoles
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_provider_can_create_organization():
    """Provider role user can create an organization."""
    user = UserFactory(role=UserRoles.PROVIDER)

    organization = create_organization(
        owner=user,
        name="My Clinic",
        phone_number="02112345678",
    )

    assert organization.owner == user
    assert organization.name == "My Clinic"
    assert organization.slug == "my-clinic"


def test_customer_cannot_create_organization():
    """Customer role user cannot create an organization."""
    user = UserFactory(role=UserRoles.CUSTOMER)

    with pytest.raises(PermissionDenied):
        create_organization(
            owner=user,
            name="Invalid Clinic",
        )


def test_create_organization_generates_unique_slug():
    """Duplicate organization names generate unique slugs with numeric suffix."""
    user = UserFactory(role=UserRoles.PROVIDER)

    first = create_organization(owner=user, name="Clinic")
    second = create_organization(owner=user, name="Clinic")

    assert first.slug == "clinic"
    assert second.slug == "clinic-2"


def test_owner_can_update_organization():
    """Organization owner can update organization details."""
    owner = UserFactory(role=UserRoles.PROVIDER)
    organization = OrganizationFactory(owner=owner, name="Old Name")

    updated = update_organization(
        organization=organization,
        actor=owner,
        name="New Name",
    )

    assert updated.name == "New Name"


def test_non_owner_cannot_update_organization():
    """Non-owner user cannot update an organization."""
    owner = UserFactory(role=UserRoles.PROVIDER)
    other_user = UserFactory(role=UserRoles.PROVIDER)
    organization = OrganizationFactory(owner=owner)

    with pytest.raises(PermissionDenied):
        update_organization(
            organization=organization,
            actor=other_user,
            name="Hacked Name",
        )
