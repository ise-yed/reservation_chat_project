from datetime import date, time, timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.appointments.services import create_appointment
from apps.availability.tests.factories import WorkingHourFactory
from apps.offerings.tests.factories import OfferingFactory
from apps.payments.enums import PaymentStatus
from apps.payments.services import (
    initiate_appointment_payment,
    mark_payment_as_paid,
    refund_payment,
)
from apps.providers.tests.factories import ProviderProfileFactory
from apps.users.enums import UserRoles
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


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


def test_customer_can_initiate_appointment_payment():
    appointment, customer, provider_user = create_ready_appointment()

    payment = initiate_appointment_payment(
        actor=customer,
        appointment_id=appointment.id,
    )

    assert payment.appointment == appointment
    assert payment.payer == customer
    assert payment.amount == appointment.price
    assert payment.status == PaymentStatus.PENDING
    assert payment.transactions.count() == 1


def test_non_customer_cannot_initiate_payment():
    appointment, customer, provider_user = create_ready_appointment()
    other_user = UserFactory(role=UserRoles.CUSTOMER)

    with pytest.raises(PermissionDenied):
        initiate_appointment_payment(
            actor=other_user,
            appointment_id=appointment.id,
        )


def test_initiate_payment_returns_existing_pending_payment():
    appointment, customer, provider_user = create_ready_appointment()

    first_payment = initiate_appointment_payment(
        actor=customer,
        appointment_id=appointment.id,
    )
    second_payment = initiate_appointment_payment(
        actor=customer,
        appointment_id=appointment.id,
    )

    assert first_payment.id == second_payment.id


@patch("apps.payments.services.payment.publish_payment_success_notification")
def test_provider_can_mark_payment_as_paid(mock_publish):
    appointment, customer, provider_user = create_ready_appointment()

    payment = initiate_appointment_payment(
        actor=customer,
        appointment_id=appointment.id,
    )

    paid_payment = mark_payment_as_paid(
        payment=payment,
        actor=provider_user,
        gateway_reference="ref-123",
    )

    assert paid_payment.status == PaymentStatus.PAID
    assert paid_payment.gateway_reference == "ref-123"
    mock_publish.assert_called_once_with(payment=paid_payment)


@patch("apps.payments.services.payment.publish_refund_success_notification")
def test_provider_can_refund_paid_payment(mock_publish):
    appointment, customer, provider_user = create_ready_appointment()

    payment = initiate_appointment_payment(
        actor=customer,
        appointment_id=appointment.id,
    )

    paid_payment = mark_payment_as_paid(
        payment=payment,
        actor=provider_user,
        gateway_reference="ref-123",
    )

    refunded_payment = refund_payment(
        payment=paid_payment,
        actor=provider_user,
        refund_reason="Customer request",
    )

    assert refunded_payment.status == PaymentStatus.REFUNDED
    mock_publish.assert_called_once_with(payment=refunded_payment)


def test_pending_payment_cannot_be_refunded():
    appointment, customer, provider_user = create_ready_appointment()

    payment = initiate_appointment_payment(
        actor=customer,
        appointment_id=appointment.id,
    )

    with pytest.raises(ValidationError):
        refund_payment(
            payment=payment,
            actor=provider_user,
        )
