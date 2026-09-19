from datetime import date, time, timedelta
from urllib.parse import urlparse

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.appointments.enums import AppointmentStatus
from apps.appointments.models import Appointment
from apps.appointments.services import expire_unpaid_appointments
from apps.availability.tests.factories import WorkingHourFactory
from apps.offerings.enums import VisitMode
from apps.offerings.tests.factories import OfferingFactory
from apps.payments.enums import PaymentMethod, PaymentStatus
from apps.payments.models import Payment
from apps.providers.tests.factories import ProviderProfileFactory
from apps.users.enums import UserRoles
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def book(customer, visit_mode=VisitMode.IN_PERSON, payment_method=None, price=100000):
    provider = ProviderProfileFactory()
    offering = OfferingFactory(
        provider=provider,
        organization=provider.organization,
        visit_mode=visit_mode,
        price=price,
        duration_minutes=30,
    )
    target_date = date.today() + timedelta(days=7)
    WorkingHourFactory(
        provider=provider,
        weekday=target_date.weekday(),
        start_time=time(9, 0),
        end_time=time(10, 0),
    )
    start_at = timezone.make_aware(
        timezone.datetime.combine(target_date, time(9, 0)), timezone.get_current_timezone()
    )
    body = {
        "provider_id": str(provider.id),
        "offering_id": str(offering.id),
        "start_at": start_at.isoformat(),
    }
    if payment_method:
        body["payment_method"] = payment_method
    response = client_for(customer).post(reverse("appointments:list-create"), body, format="json")
    return provider, response


def follow(client, pay_url, **replace):
    parsed = urlparse(pay_url)
    query = parsed.query
    for old, new in replace.items():
        query = query.replace(old, new)
    return client.get(f"{parsed.path}?{query}")


def test_in_person_visit_paid_at_clinic():
    customer = UserFactory(role=UserRoles.CUSTOMER)
    provider, response = book(customer, payment_method=PaymentMethod.IN_PERSON)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["status"] == AppointmentStatus.CONFIRMED
    assert "pay_url" not in response.data
    assert response.data["payment"]["method"] == PaymentMethod.IN_PERSON
    assert response.data["payment"]["status"] == PaymentStatus.PENDING

    # provider confirms the cash/card payment at the clinic
    payment_id = response.data["payment"]["id"]
    url = reverse("payments:mark-paid", kwargs={"pk": payment_id})
    assert client_for(customer).post(url).status_code == status.HTTP_403_FORBIDDEN
    result = client_for(provider.user).post(url)
    assert result.status_code == status.HTTP_200_OK
    assert result.data["status"] == PaymentStatus.PAID


def test_online_visit_cannot_be_paid_in_person():
    customer = UserFactory(role=UserRoles.CUSTOMER)
    _, response = book(customer, VisitMode.ONLINE_CHAT, PaymentMethod.IN_PERSON)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert Payment.objects.count() == 0


def test_online_payment_confirms_appointment_and_creates_conversation():
    customer = UserFactory(role=UserRoles.CUSTOMER)
    _, response = book(customer, VisitMode.ONLINE_CHAT)  # default = online

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["status"] == AppointmentStatus.PENDING  # slot held, awaiting payment
    assert response.data["pay_url"]

    appointment = Appointment.objects.get(id=response.data["id"])
    assert appointment.conversation_id is None

    result = follow(APIClient(), response.data["pay_url"])  # gateway callback (no JWT)
    assert result.status_code == status.HTTP_200_OK
    assert result.data["status"] == PaymentStatus.PAID

    appointment.refresh_from_db()
    assert appointment.status == AppointmentStatus.CONFIRMED
    assert appointment.conversation_id is not None

    # callback replay is idempotent
    assert follow(APIClient(), response.data["pay_url"]).data["status"] == PaymentStatus.PAID


def test_failed_online_payment_can_be_retried():
    customer = UserFactory(role=UserRoles.CUSTOMER)
    _, response = book(customer, payment_method=PaymentMethod.ONLINE)

    failed = follow(APIClient(), response.data["pay_url"], OK="NOK")
    assert failed.data["status"] == PaymentStatus.FAILED
    assert Appointment.objects.get(id=response.data["id"]).status == AppointmentStatus.PENDING

    payment_id = response.data["payment"]["id"]
    retry = client_for(customer).post(reverse("payments:pay", kwargs={"pk": payment_id}))
    assert retry.status_code == status.HTTP_200_OK
    assert follow(APIClient(), retry.data["pay_url"]).data["status"] == PaymentStatus.PAID
    assert Appointment.objects.get(id=response.data["id"]).status == AppointmentStatus.CONFIRMED


def test_provider_cannot_confirm_unpaid_online_appointment():
    customer = UserFactory(role=UserRoles.CUSTOMER)
    provider, response = book(customer)
    url = reverse("appointments:status-update", kwargs={"pk": response.data["id"]})
    result = client_for(provider.user).patch(url, {"status": "confirmed"}, format="json")
    assert result.status_code == status.HTTP_400_BAD_REQUEST


def test_unpaid_online_appointment_expires_and_releases_slot():
    customer = UserFactory(role=UserRoles.CUSTOMER)
    _, response = book(customer)
    Appointment.objects.filter(id=response.data["id"]).update(
        created_at=timezone.now() - timedelta(minutes=30)
    )

    assert expire_unpaid_appointments() == 1

    appointment = Appointment.objects.get(id=response.data["id"])
    assert appointment.status == AppointmentStatus.CANCELLED_BY_CUSTOMER
    assert appointment.payment.status == PaymentStatus.CANCELLED

    # paying after expiry must fail and never confirm the appointment
    late = follow(APIClient(), response.data["pay_url"])
    assert late.status_code == status.HTTP_400_BAD_REQUEST
