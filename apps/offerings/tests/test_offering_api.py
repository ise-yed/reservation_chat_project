import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.offerings.tests.factories import OfferingFactory
from apps.organizations.tests.factories import OrganizationFactory
from apps.providers.tests.factories import ProviderProfileFactory
from apps.users.enums import UserRoles
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def get_client(user=None):
    client = APIClient()
    if user:
        client.force_authenticate(user=user)
    return client


class TestOfferingListCreateAPI:
    def test_authenticated_user_can_list_active_offerings(self):
        user = UserFactory()
        OfferingFactory(title="Active Offering", is_active=True)
        OfferingFactory(title="Inactive Offering", is_active=False)

        client = get_client(user)
        url = reverse("offerings:list-create")

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == "Active Offering"

    def test_unauthenticated_user_cannot_list_offerings(self):
        client = get_client()
        url = reverse("offerings:list-create")

        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_organization_owner_can_create_offering(self):
        owner = UserFactory(role=UserRoles.PROVIDER)
        organization = OrganizationFactory(owner=owner)
        provider = ProviderProfileFactory(organization=organization)

        client = get_client(owner)
        url = reverse("offerings:list-create")

        payload = {
            "organization_id": str(organization.id),
            "provider_id": str(provider.id),
            "title": "General Visit",
            "description": "General visit description",
            "duration_minutes": 30,
            "buffer_before_minutes": 0,
            "buffer_after_minutes": 10,
            "price": "100000.00",
            "requires_approval": False,
            "is_active": True,
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "General Visit"
        assert response.data["organization"]["id"] == str(organization.id)
        assert response.data["provider"]["id"] == str(provider.id)

    def test_non_owner_cannot_create_offering(self):
        owner = UserFactory(role=UserRoles.PROVIDER)
        other_user = UserFactory(role=UserRoles.PROVIDER)
        organization = OrganizationFactory(owner=owner)
        provider = ProviderProfileFactory(organization=organization)

        client = get_client(other_user)
        url = reverse("offerings:list-create")

        payload = {
            "organization_id": str(organization.id),
            "provider_id": str(provider.id),
            "title": "Invalid Offering",
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestMyOfferingListAPI:
    def test_provider_user_can_list_own_offerings(self):
        provider_user = UserFactory(role=UserRoles.PROVIDER)
        provider = ProviderProfileFactory(user=provider_user)
        other_provider = ProviderProfileFactory()

        OfferingFactory(provider=provider, title="Mine")
        OfferingFactory(provider=other_provider, title="Other")

        client = get_client(provider_user)
        url = reverse("offerings:my-list")

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == "Mine"


class TestOrganizationOfferingListAPI:
    def test_user_can_list_active_organization_offerings(self):
        user = UserFactory()
        organization = OrganizationFactory(is_active=True)
        provider = ProviderProfileFactory(organization=organization)

        OfferingFactory(
            organization=organization,
            provider=provider,
            title="Active",
            is_active=True,
        )
        OfferingFactory(
            organization=organization,
            provider=provider,
            title="Inactive",
            is_active=False,
        )

        client = get_client(user)
        url = reverse(
            "offerings:organization-list",
            kwargs={"organization_id": organization.id},
        )

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == "Active"

    def test_organization_owner_can_see_inactive_organization_offerings(self):
        owner = UserFactory(role=UserRoles.PROVIDER)
        organization = OrganizationFactory(owner=owner)
        provider = ProviderProfileFactory(organization=organization)

        OfferingFactory(
            organization=organization,
            provider=provider,
            title="Active",
            is_active=True,
        )
        OfferingFactory(
            organization=organization,
            provider=provider,
            title="Inactive",
            is_active=False,
        )

        client = get_client(owner)
        url = reverse(
            "offerings:organization-list",
            kwargs={"organization_id": organization.id},
        )

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2


class TestProviderOfferingListAPI:
    def test_user_can_list_active_provider_offerings(self):
        user = UserFactory()
        provider = ProviderProfileFactory(is_active=True)

        OfferingFactory(provider=provider, title="Active", is_active=True)
        OfferingFactory(provider=provider, title="Inactive", is_active=False)

        client = get_client(user)
        url = reverse(
            "offerings:provider-list",
            kwargs={"provider_id": provider.id},
        )

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == "Active"


class TestOfferingDetailAPI:
    def test_user_can_retrieve_active_offering(self):
        user = UserFactory()
        offering = OfferingFactory(is_active=True)

        client = get_client(user)
        url = reverse("offerings:detail", kwargs={"pk": offering.id})

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(offering.id)

    def test_organization_owner_can_update_offering(self):
        owner = UserFactory(role=UserRoles.PROVIDER)
        organization = OrganizationFactory(owner=owner)
        provider = ProviderProfileFactory(organization=organization)
        offering = OfferingFactory(
            organization=organization,
            provider=provider,
            title="Old Offering",
        )

        client = get_client(owner)
        url = reverse("offerings:detail", kwargs={"pk": offering.id})

        response = client.patch(
            url,
            {
                "title": "New Offering",
                "price": "200000.00",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "New Offering"
        assert response.data["price"] == "200000.00"

    def test_non_owner_cannot_update_offering(self):
        owner = UserFactory(role=UserRoles.PROVIDER)
        other_user = UserFactory(role=UserRoles.PROVIDER)
        organization = OrganizationFactory(owner=owner)
        provider = ProviderProfileFactory(organization=organization)
        offering = OfferingFactory(
            organization=organization,
            provider=provider,
        )

        client = get_client(other_user)
        url = reverse("offerings:detail", kwargs={"pk": offering.id})

        response = client.patch(
            url,
            {"title": "Invalid"},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
