"""
Tests for Organization and Branch model string representations.
"""

import pytest

from apps.organizations.tests.factories import BranchFactory, OrganizationFactory

pytestmark = pytest.mark.django_db


def test_organization_str_returns_name():
    """Organization string representation should return its name."""
    organization = OrganizationFactory(name="Clinic A")

    assert str(organization) == "Clinic A"


def test_branch_str_returns_organization_and_branch_name():
    """Branch string representation should return 'Organization - Branch' format."""
    organization = OrganizationFactory(name="Clinic A")
    branch = BranchFactory(organization=organization, name="Main Branch")

    assert str(branch) == "Clinic A - Main Branch"
