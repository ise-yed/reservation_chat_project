from datetime import date, time, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.appointments.enums import AppointmentStatus
from apps.appointments.services import create_appointment
from apps.availability.tests.factories import WorkingHourFactory
from apps.offerings.tests.factories import OfferingFactory
from apps.providers.tests.factories import ProviderProfileFactory
from apps.users.enums import UserRoles
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def get_client(user=None):
    client = APIClient()
    if user:
        client.force_authenticate(user=user)
    return client


def make_aware_datetime(target_date, target_time):
    current_timezone = timezone.get_current_timezone()
    return timezone.make_aware(
        timezone.datetime.combine(target_date, target_time),
        current_timezone,
    )


class TestAppointmentCreateAPI:
    def test_customer_can_create_appointment(self):
        customer = UserFactory(role=UserRoles.CUSTOMER)
        provider = ProviderProfileFactory()
        offering = OfferingFactory(
            provider=provider,
            organization=provider.organization,
            duration_minutes=30,
        )

        target_date = date.today() + timedelta(days=7)

        WorkingHourFactory(
            provider=provider,
            weekday=target_date.weekday(),
            start_time=time(9, 0),
            end_time=time(10, 0),
        )

        start_at = make_aware_datetime(target_date, time(9, 0))

        client = get_client(customer)
        url = reverse("appointments:list-create")

        response = client.post(
            url,
            {
                "provider_id": str(provider.id),
                "offering_id": str(offering.id),
                "start_at": start_at.isoformat(),
                "notes": "Test appointment",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["customer"]["id"] == str(customer.id)
        assert response.data["provider"]["id"] == str(provider.id)

    def test_unauthenticated_user_cannot_create_appointment(self):
        client = get_client()
        url = reverse("appointments:list-create")

        response = client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAppointmentListAPI:
    def test_customer_can_list_own_appointments(self):
        customer = UserFactory(role=UserRoles.CUSTOMER)
        provider = ProviderProfileFactory()
        offering = OfferingFactory(provider=provider, organization=provider.organization)

        target_date = date.today() + timedelta(days=7)

        WorkingHourFactory(
            provider=provider,
            weekday=target_date.weekday(),
            start_time=time(9, 0),
            end_time=time(10, 0),
        )

        create_appointment(
            customer=customer,
            provider_id=provider.id,
            offering_id=offering.id,
            start_at=make_aware_datetime(target_date, time(9, 0)),
        )

        client = get_client(customer)
        url = reverse("appointments:my-list")

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_provider_can_list_own_provider_appointments(self):
        customer = UserFactory(role=UserRoles.CUSTOMER)
        provider_user = UserFactory(role=UserRoles.PROVIDER)
        provider = ProviderProfileFactory(user=provider_user)
        offering = OfferingFactory(provider=provider, organization=provider.organization)

        target_date = date.today() + timedelta(days=7)

        WorkingHourFactory(
            provider=provider,
            weekday=target_date.weekday(),
            start_time=time(9, 0),
            end_time=time(10, 0),
        )

        create_appointment(
            customer=customer,
            provider_id=provider.id,
            offering_id=offering.id,
            start_at=make_aware_datetime(target_date, time(9, 0)),
        )

        client = get_client(provider_user)
        url = reverse(
            "appointments:provider-list",
            kwargs={"provider_id": provider.id},
        )

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1


class TestAppointmentActionsAPI:
    def test_customer_can_cancel_own_appointment(self):
        customer = UserFactory(role=UserRoles.CUSTOMER)
        provider = ProviderProfileFactory()
        offering = OfferingFactory(provider=provider, organization=provider.organization)

        target_date = date.today() + timedelta(days=7)

        WorkingHourFactory(
            provider=provider,
            weekday=target_date.weekday(),
            start_time=time(9, 0),
            end_time=time(10, 0),
        )

        appointment = create_appointment(
            customer=customer,
            provider_id=provider.id,
            offering_id=offering.id,
            start_at=make_aware_datetime(target_date, time(9, 0)),
        )

        client = get_client(customer)
        url = reverse("appointments:cancel", kwargs={"pk": appointment.id})

        response = client.post(
            url,
            {"cancel_reason": "Changed plan"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == AppointmentStatus.CANCELLED_BY_CUSTOMER

    def test_provider_can_update_appointment_status(self):
        customer = UserFactory(role=UserRoles.CUSTOMER)
        provider_user = UserFactory(role=UserRoles.PROVIDER)
        provider = ProviderProfileFactory(user=provider_user)
        offering = OfferingFactory(provider=provider, organization=provider.organization)

        target_date = date.today() + timedelta(days=7)

        WorkingHourFactory(
            provider=provider,
            weekday=target_date.weekday(),
            start_time=time(9, 0),
            end_time=time(10, 0),
        )

        appointment = create_appointment(
            customer=customer,
            provider_id=provider.id,
            offering_id=offering.id,
            start_at=make_aware_datetime(target_date, time(9, 0)),
        )

        client = get_client(provider_user)
        url = reverse("appointments:status-update", kwargs={"pk": appointment.id})

        response = client.patch(
            url,
            {"status": AppointmentStatus.COMPLETED},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == AppointmentStatus.COMPLETED
