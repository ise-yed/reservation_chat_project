"""
Tests for branch service layer operations.
"""

import pytest
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.organizations.services import create_branch, update_branch
from apps.organizations.tests.factories import BranchFactory, OrganizationFactory
from apps.users.enums import UserRoles
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_owner_can_create_branch():
    """Organization owner can create a new branch."""
    owner = UserFactory(role=UserRoles.PROVIDER)
    organization = OrganizationFactory(owner=owner)

    branch = create_branch(
        organization=organization,
        actor=owner,
        name="Main Branch",
    )

    assert branch.organization == organization
    assert branch.name == "Main Branch"


def test_duplicate_branch_name_is_not_allowed():
    """Creating a branch with duplicate name (case-insensitive) raises error."""
    owner = UserFactory(role=UserRoles.PROVIDER)
    organization = OrganizationFactory(owner=owner)
    BranchFactory(organization=organization, name="Main Branch")

    with pytest.raises(ValidationError):
        create_branch(
            organization=organization,
            actor=owner,
            name="main branch",
        )


def test_owner_can_update_branch():
    """Organization owner can update branch details."""
    owner = UserFactory(role=UserRoles.PROVIDER)
    organization = OrganizationFactory(owner=owner)
    branch = BranchFactory(organization=organization, name="Old Branch")

    updated = update_branch(
        branch=branch,
        actor=owner,
        name="New Branch",
    )

    assert updated.name == "New Branch"


def test_non_owner_cannot_update_branch():
    """Non-owner user cannot update a branch."""
    owner = UserFactory(role=UserRoles.PROVIDER)
    other_user = UserFactory(role=UserRoles.PROVIDER)
    organization = OrganizationFactory(owner=owner)
    branch = BranchFactory(organization=organization)

    with pytest.raises(PermissionDenied):
        update_branch(
            branch=branch,
            actor=other_user,
            name="Invalid",
        )
