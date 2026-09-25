"""
API view tests for Organization and Branch endpoints.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.organizations.tests.factories import BranchFactory, OrganizationFactory
from apps.users.enums import UserRoles
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def get_client(user=None):
    """Return authenticated client if user provided, otherwise unauthenticated."""
    client = APIClient()
    if user:
        client.force_authenticate(user=user)
    return client


class TestOrganizationListCreateAPI:
    """Tests for organization list and create endpoints."""

    def test_authenticated_user_can_list_active_organizations(self):
        """Authenticated user can only see active organizations."""
        user = UserFactory()
        OrganizationFactory(name="Active Org", is_active=True)
        OrganizationFactory(name="Inactive Org", is_active=False)

        client = get_client(user)
        url = reverse("organizations:list-create")

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Active Org"

    def test_unauthenticated_user_cannot_list_organizations(self):
        """Unauthenticated user cannot list organizations."""
        client = get_client()
        url = reverse("organizations:list-create")

        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_can_create_organization(self):
        """Admin user can create an organization."""
        admin = UserFactory(role=UserRoles.SUPER_ADMIN, is_staff=True)
        client = get_client(admin)
        url = reverse("organizations:list-create")

        payload = {
            "name": "New Clinic",
            "description": "Clinic description",
            "phone_number": "02112345678",
            "email": "clinic@example.com",
            "website": "https://example.com",
            "timezone": "Asia/Tehran",
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Clinic"

    def test_customer_cannot_create_organization(self):
        """Customer role user cannot create an organization."""
        user = UserFactory(role=UserRoles.CUSTOMER)
        client = get_client(user)
        url = reverse("organizations:list-create")

        response = client.post(url, {"name": "Invalid Org"}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestMyOrganizationAPI:
    """Tests for my-organizations endpoint."""

    def test_user_can_list_only_owned_organizations(self):
        """User can only see organizations they own."""
        owner = UserFactory(role=UserRoles.PROVIDER)
        other_user = UserFactory(role=UserRoles.PROVIDER)

        OrganizationFactory(owner=owner, name="Mine")
        OrganizationFactory(owner=other_user, name="Other")

        client = get_client(owner)
        url = reverse("organizations:my-list")

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Mine"


class TestOrganizationDetailAPI:
    """Tests for organization detail, update endpoints."""

    def test_user_can_retrieve_active_organization(self):
        """Any authenticated user can view an active organization."""
        user = UserFactory()
        organization = OrganizationFactory(is_active=True)
        client = get_client(user)

        url = reverse("organizations:detail", kwargs={"pk": organization.id})

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(organization.id)

    def test_owner_can_update_organization(self):
        """Organization owner can update their organization."""
        owner = UserFactory(role=UserRoles.PROVIDER)
        organization = OrganizationFactory(owner=owner, name="Old Name")
        client = get_client(owner)

        url = reverse("organizations:detail", kwargs={"pk": organization.id})

        response = client.patch(
            url,
            {"name": "New Name"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "New Name"

    def test_non_owner_cannot_update_organization(self):
        """Non-owner user cannot update an organization."""
        owner = UserFactory(role=UserRoles.PROVIDER)
        other_user = UserFactory(role=UserRoles.PROVIDER)
        organization = OrganizationFactory(owner=owner)
        client = get_client(other_user)

        url = reverse("organizations:detail", kwargs={"pk": organization.id})

        response = client.patch(
            url,
            {"name": "Invalid Name"},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestBranchAPI:
    """Tests for branch list, create, update endpoints."""

    def test_user_can_list_active_branches(self):
        """Authenticated user can only see active branches."""
        user = UserFactory()
        organization = OrganizationFactory(is_active=True)
        BranchFactory(organization=organization, name="Active Branch", is_active=True)
        BranchFactory(organization=organization, name="Inactive Branch", is_active=False)

        client = get_client(user)
        url = reverse(
            "organizations:branch-list-create",
            kwargs={"organization_id": organization.id},
        )

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Active Branch"

    def test_owner_can_create_branch(self):
        """Organization owner can create a branch."""
        owner = UserFactory(role=UserRoles.PROVIDER)
        organization = OrganizationFactory(owner=owner)
        client = get_client(owner)

        url = reverse(
            "organizations:branch-list-create",
            kwargs={"organization_id": organization.id},
        )

        payload = {
            "name": "Main Branch",
            "address": "Main address",
            "phone_number": "02112345678",
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Main Branch"

    def test_non_owner_cannot_create_branch(self):
        """Non-owner user cannot create a branch."""
        owner = UserFactory(role=UserRoles.PROVIDER)
        other_user = UserFactory(role=UserRoles.PROVIDER)
        organization = OrganizationFactory(owner=owner)
        client = get_client(other_user)

        url = reverse(
            "organizations:branch-list-create",
            kwargs={"organization_id": organization.id},
        )

        response = client.post(
            url,
            {"name": "Invalid Branch"},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_owner_can_update_branch(self):
        """Organization owner can update a branch."""
        owner = UserFactory(role=UserRoles.PROVIDER)
        organization = OrganizationFactory(owner=owner)
        branch = BranchFactory(organization=organization, name="Old Branch")
        client = get_client(owner)

        url = reverse(
            "organizations:branch-detail",
            kwargs={"pk": branch.id},
        )

        response = client.patch(
            url,
            {"name": "New Branch"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "New Branch"

    def test_non_owner_cannot_update_branch(self):
        """Non-owner user cannot update a branch."""
        owner = UserFactory(role=UserRoles.PROVIDER)
        other_user = UserFactory(role=UserRoles.PROVIDER)
        organization = OrganizationFactory(owner=owner)
        branch = BranchFactory(organization=organization)
        client = get_client(other_user)

        url = reverse(
            "organizations:branch-detail",
            kwargs={"pk": branch.id},
        )

        response = client.patch(
            url,
            {"name": "Invalid"},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
