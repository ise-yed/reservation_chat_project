import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.organizations.tests.factories import BranchFactory, OrganizationFactory
from apps.providers.tests.factories import ProviderProfileFactory
from apps.users.enums import UserRoles
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def get_client(user=None):
    client = APIClient()
    if user:
        client.force_authenticate(user=user)
    return client


class TestProviderProfileListCreateAPI:
    def test_authenticated_user_can_list_active_providers(self):
        user = UserFactory()
        ProviderProfileFactory(is_active=True)
        ProviderProfileFactory(is_active=False)

        client = get_client(user)
        url = reverse("providers:list-create")

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert isinstance(response.data["results"][0]["specialties"], list)

    def test_unauthenticated_user_cannot_list_providers(self):
        client = get_client()
        url = reverse("providers:list-create")

        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_organization_owner_can_create_provider_profile(self):
        owner = UserFactory(role=UserRoles.PROVIDER)
        provider_user = UserFactory(role=UserRoles.PROVIDER)
        organization = OrganizationFactory(owner=owner)
        branch = BranchFactory(organization=organization)

        client = get_client(owner)
        url = reverse("providers:list-create")

        payload = {
            "user_id": str(provider_user.id),
            "organization_id": str(organization.id),
            "branch_id": str(branch.id),
            "title": "Dr.",
            "specialty_ids": [],
            "bio": "Provider bio",
            "default_slot_duration_minutes": 30,
            "is_active": True,
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["user"]["id"] == str(provider_user.id)
        assert response.data["organization"]["id"] == str(organization.id)
        assert response.data["branch"]["id"] == str(branch.id)

    def test_non_owner_cannot_create_provider_profile(self):
        owner = UserFactory(role=UserRoles.PROVIDER)
        other_user = UserFactory(role=UserRoles.PROVIDER)
        provider_user = UserFactory(role=UserRoles.PROVIDER)
        organization = OrganizationFactory(owner=owner)

        client = get_client(other_user)
        url = reverse("providers:list-create")

        payload = {
            "user_id": str(provider_user.id),
            "organization_id": str(organization.id),
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestMyProviderProfilesAPI:
    def test_user_can_list_own_provider_profiles(self):
        provider_user = UserFactory(role=UserRoles.PROVIDER)
        other_provider = UserFactory(role=UserRoles.PROVIDER)

        ProviderProfileFactory(user=provider_user)
        ProviderProfileFactory(user=other_provider)

        client = get_client(provider_user)
        url = reverse("providers:my-list")

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert isinstance(response.data["results"][0]["specialties"], list)


class TestOrganizationProvidersAPI:
    def test_user_can_list_active_organization_providers(self):
        user = UserFactory()
        organization = OrganizationFactory(is_active=True)

        ProviderProfileFactory(
            organization=organization,
            is_active=True,
        )
        ProviderProfileFactory(
            organization=organization,
            is_active=False,
        )

        client = get_client(user)
        url = reverse(
            "providers:organization-list",
            kwargs={"organization_id": organization.id},
        )

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_organization_owner_can_see_inactive_organization_providers(self):
        owner = UserFactory(role=UserRoles.PROVIDER)
        organization = OrganizationFactory(owner=owner, is_active=True)

        ProviderProfileFactory(
            organization=organization,
            is_active=True,
        )
        ProviderProfileFactory(
            organization=organization,
            is_active=False,
        )

        client = get_client(owner)
        url = reverse(
            "providers:organization-list",
            kwargs={"organization_id": organization.id},
        )

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2


class TestProviderProfileDetailAPI:
    def test_user_can_retrieve_active_provider_profile(self):
        user = UserFactory()
        provider_profile = ProviderProfileFactory(is_active=True)

        client = get_client(user)
        url = reverse("providers:detail", kwargs={"pk": provider_profile.id})

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(provider_profile.id)

    def test_provider_can_update_own_public_profile_fields(self):
        provider_user = UserFactory(role=UserRoles.PROVIDER)
        provider_profile = ProviderProfileFactory(
            user=provider_user,
            title="Old",
        )

        client = get_client(provider_user)
        url = reverse("providers:detail", kwargs={"pk": provider_profile.id})

        response = client.patch(
            url,
            {
                "title": "New",
                "specialty_ids": [],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "New"
        assert response.data["specialties"] == []

    def test_provider_cannot_update_own_is_active_field(self):
        provider_user = UserFactory(role=UserRoles.PROVIDER)
        provider_profile = ProviderProfileFactory(
            user=provider_user,
            is_active=True,
        )

        client = get_client(provider_user)
        url = reverse("providers:detail", kwargs={"pk": provider_profile.id})

        response = client.patch(
            url,
            {"is_active": False},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_organization_owner_can_update_provider_branch(self):
        owner = UserFactory(role=UserRoles.PROVIDER)
        provider_user = UserFactory(role=UserRoles.PROVIDER)
        organization = OrganizationFactory(owner=owner)

        old_branch = BranchFactory(organization=organization)
        new_branch = BranchFactory(organization=organization)

        provider_profile = ProviderProfileFactory(
            user=provider_user,
            organization=organization,
            branch=old_branch,
        )

        client = get_client(owner)
        url = reverse("providers:detail", kwargs={"pk": provider_profile.id})

        response = client.patch(
            url,
            {"branch_id": str(new_branch.id)},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["branch"]["id"] == str(new_branch.id)

    def test_non_manager_cannot_update_provider_profile(self):
        owner = UserFactory(role=UserRoles.PROVIDER)
        other_user = UserFactory(role=UserRoles.PROVIDER)
        provider_user = UserFactory(role=UserRoles.PROVIDER)
        organization = OrganizationFactory(owner=owner)

        provider_profile = ProviderProfileFactory(
            user=provider_user,
            organization=organization,
        )

        client = get_client(other_user)
        url = reverse("providers:detail", kwargs={"pk": provider_profile.id})

        response = client.patch(
            url,
            {"title": "Invalid"},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
