from datetime import date, time, timedelta

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.availability.tests.factories import WorkingHourFactory
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


class TestWorkingHourAPI:
    def test_provider_user_can_create_working_hour(self):
        provider_user = UserFactory(role=UserRoles.PROVIDER)
        provider = ProviderProfileFactory(user=provider_user)

        client = get_client(provider_user)
        url = reverse("availability:working-hour-list-create")

        payload = {
            "provider_id": str(provider.id),
            "weekday": 0,
            "start_time": "09:00:00",
            "end_time": "12:00:00",
            "is_active": True,
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["provider"]["id"] == str(provider.id)
        assert response.data["weekday"] == 0

    def test_non_manager_cannot_create_working_hour(self):
        other_user = UserFactory(role=UserRoles.PROVIDER)
        provider = ProviderProfileFactory()

        client = get_client(other_user)
        url = reverse("availability:working-hour-list-create")

        payload = {
            "provider_id": str(provider.id),
            "weekday": 0,
            "start_time": "09:00:00",
            "end_time": "12:00:00",
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_can_list_provider_working_hours(self):
        user = UserFactory()
        provider = ProviderProfileFactory()
        WorkingHourFactory(provider=provider, weekday=0)

        client = get_client(user)
        url = reverse(
            "availability:provider-working-hour-list",
            kwargs={"provider_id": provider.id},
        )

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1


class TestAvailableSlotsAPI:
    def test_user_can_get_available_slots(self):
        user = UserFactory()
        provider_user = UserFactory(role=UserRoles.PROVIDER)
        provider = ProviderProfileFactory(user=provider_user)
        offering = OfferingFactory(
            provider=provider,
            organization=provider.organization,
            duration_minutes=30,
            buffer_before_minutes=0,
            buffer_after_minutes=0,
        )

        target_date = date.today() + timedelta(days=7)

        WorkingHourFactory(
            provider=provider,
            weekday=target_date.weekday(),
            start_time=time(9, 0),
            end_time=time(10, 0),
        )

        client = get_client(user)
        url = reverse("availability:available-slots")

        response = client.get(
            url,
            {
                "provider_id": str(provider.id),
                "offering_id": str(offering.id),
                "date": target_date.isoformat(),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2


class TestHolidayAPI:
    def test_organization_owner_can_create_holiday(self):
        owner = UserFactory(role=UserRoles.PROVIDER)
        organization = OrganizationFactory(owner=owner)

        client = get_client(owner)
        url = reverse("availability:holiday-list-create")

        payload = {
            "organization_id": str(organization.id),
            "date": (date.today() + timedelta(days=1)).isoformat(),
            "title": "Holiday",
            "is_active": True,
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["organization"]["id"] == str(organization.id)

    def test_non_owner_cannot_create_holiday(self):
        owner = UserFactory(role=UserRoles.PROVIDER)
        other_user = UserFactory(role=UserRoles.PROVIDER)
        organization = OrganizationFactory(owner=owner)

        client = get_client(other_user)
        url = reverse("availability:holiday-list-create")

        payload = {
            "organization_id": str(organization.id),
            "date": (date.today() + timedelta(days=1)).isoformat(),
            "title": "Invalid Holiday",
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN
