from datetime import date, time, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.appointments.services import create_appointment
from apps.availability.tests.factories import WorkingHourFactory
from apps.offerings.tests.factories import OfferingFactory
from apps.payments.enums import PaymentStatus
from apps.payments.services import initiate_appointment_payment
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


def create_ready_appointment():
    customer = UserFactory(role=UserRoles.CUSTOMER)
    provider_user = UserFactory(role=UserRoles.PROVIDER)
    provider = ProviderProfileFactory(user=provider_user)

    offering = OfferingFactory(
        provider=provider,
        organization=provider.organization,
        duration_minutes=30,
        price=100000,
    )

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

    return appointment, customer, provider_user


def test_customer_can_create_payment_for_appointment():
    appointment, customer, provider_user = create_ready_appointment()

    client = get_client(customer)
    url = reverse("payments:appointment-payment-create")

    response = client.post(
        url,
        {
            "appointment_id": str(appointment.id),
            "method": "mock",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["appointment"]["id"] == str(appointment.id)
    assert response.data["status"] == PaymentStatus.PENDING


def test_customer_can_list_own_payments():
    appointment, customer, provider_user = create_ready_appointment()

    initiate_appointment_payment(
        actor=customer,
        appointment_id=appointment.id,
    )

    client = get_client(customer)
    url = reverse("payments:my-list")

    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1


def test_provider_can_mark_payment_as_paid():
    appointment, customer, provider_user = create_ready_appointment()

    payment = initiate_appointment_payment(
        actor=customer,
        appointment_id=appointment.id,
    )

    client = get_client(provider_user)
    url = reverse("payments:mark-paid", kwargs={"pk": payment.id})

    response = client.post(
        url,
        {
            "gateway_reference": "ref-123",
            "raw_response": {"status": "ok"},
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == PaymentStatus.PAID
    assert response.data["gateway_reference"] == "ref-123"


def test_customer_cannot_mark_payment_as_paid():
    appointment, customer, provider_user = create_ready_appointment()

    payment = initiate_appointment_payment(
        actor=customer,
        appointment_id=appointment.id,
    )

    client = get_client(customer)
    url = reverse("payments:mark-paid", kwargs={"pk": payment.id})

    response = client.post(
        url,
        {"gateway_reference": "ref-123"},
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
