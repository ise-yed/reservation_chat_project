from datetime import date, time, timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.appointments.enums import AppointmentStatus
from apps.appointments.services import (
    cancel_appointment,
    create_appointment,
    update_appointment_status,
)
from apps.availability.tests.factories import WorkingHourFactory
from apps.offerings.tests.factories import OfferingFactory
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


def test_customer_can_create_appointment():
    customer = UserFactory(role=UserRoles.CUSTOMER)
    provider_user = UserFactory(role=UserRoles.PROVIDER)
    provider = ProviderProfileFactory(user=provider_user)

    offering = OfferingFactory(
        provider=provider,
        organization=provider.organization,
        duration_minutes=30,
        buffer_before_minutes=0,
        buffer_after_minutes=0,
        requires_approval=False,
        is_active=True,
    )

    target_date = date.today() + timedelta(days=7)

    WorkingHourFactory(
        provider=provider,
        weekday=target_date.weekday(),
        start_time=time(9, 0),
        end_time=time(10, 0),
    )

    start_at = make_aware_datetime(target_date, time(9, 0))

    appointment = create_appointment(
        customer=customer,
        provider_id=provider.id,
        offering_id=offering.id,
        start_at=start_at,
        notes="Test",
    )

    assert appointment.customer == customer
    assert appointment.provider == provider
    assert appointment.offering == offering
    assert appointment.status == AppointmentStatus.CONFIRMED
    assert appointment.end_at == start_at + timedelta(minutes=30)


def test_duplicate_appointment_slot_is_not_allowed():
    customer_1 = UserFactory(role=UserRoles.CUSTOMER)
    customer_2 = UserFactory(role=UserRoles.CUSTOMER)
    provider = ProviderProfileFactory()

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

    start_at = make_aware_datetime(target_date, time(9, 0))

    create_appointment(
        customer=customer_1,
        provider_id=provider.id,
        offering_id=offering.id,
        start_at=start_at,
    )

    with pytest.raises(ValidationError):
        create_appointment(
            customer=customer_2,
            provider_id=provider.id,
            offering_id=offering.id,
            start_at=start_at,
        )


def test_back_to_back_appointments_are_allowed():
    customer_1 = UserFactory(role=UserRoles.CUSTOMER)
    customer_2 = UserFactory(role=UserRoles.CUSTOMER)
    provider = ProviderProfileFactory()

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

    first_start = make_aware_datetime(target_date, time(9, 0))
    second_start = make_aware_datetime(target_date, time(9, 30))

    first = create_appointment(
        customer=customer_1,
        provider_id=provider.id,
        offering_id=offering.id,
        start_at=first_start,
    )

    second = create_appointment(
        customer=customer_2,
        provider_id=provider.id,
        offering_id=offering.id,
        start_at=second_start,
    )

    assert first.id != second.id


def test_appointment_requires_pending_status_when_offering_requires_approval():
    customer = UserFactory(role=UserRoles.CUSTOMER)
    provider = ProviderProfileFactory()

    offering = OfferingFactory(
        provider=provider,
        organization=provider.organization,
        duration_minutes=30,
        requires_approval=True,
    )

    target_date = date.today() + timedelta(days=7)

    WorkingHourFactory(
        provider=provider,
        weekday=target_date.weekday(),
        start_time=time(9, 0),
        end_time=time(10, 0),
    )

    start_at = make_aware_datetime(target_date, time(9, 0))

    appointment = create_appointment(
        customer=customer,
        provider_id=provider.id,
        offering_id=offering.id,
        start_at=start_at,
    )

    assert appointment.status == AppointmentStatus.PENDING


def test_customer_can_cancel_own_appointment():
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

    cancelled = cancel_appointment(
        appointment=appointment,
        actor=customer,
        cancel_reason="Changed plan",
    )

    assert cancelled.status == AppointmentStatus.CANCELLED_BY_CUSTOMER
    assert cancelled.cancelled_by == customer


def test_non_related_user_cannot_cancel_appointment():
    customer = UserFactory(role=UserRoles.CUSTOMER)
    other_user = UserFactory(role=UserRoles.CUSTOMER)
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

    with pytest.raises(PermissionDenied):
        cancel_appointment(
            appointment=appointment,
            actor=other_user,
        )


def test_provider_can_complete_appointment():
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

    updated = update_appointment_status(
        appointment=appointment,
        actor=provider_user,
        status=AppointmentStatus.COMPLETED,
    )

    assert updated.status == AppointmentStatus.COMPLETED


@patch("apps.appointments.services.appointment.publish_appointment_created_notification")
def test_create_appointment_publishes_created_notification(mock_publish):
    customer = UserFactory(role=UserRoles.CUSTOMER)
    provider = ProviderProfileFactory()

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

    appointment = create_appointment(
        customer=customer,
        provider_id=provider.id,
        offering_id=offering.id,
        start_at=make_aware_datetime(target_date, time(9, 0)),
    )

    mock_publish.assert_called_once_with(appointment=appointment)


@patch("apps.appointments.services.appointment.publish_appointment_cancelled_notification")
def test_cancel_appointment_publishes_cancelled_notification(mock_publish):
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

    cancelled = cancel_appointment(
        appointment=appointment,
        actor=customer,
        cancel_reason="Changed plan",
    )

    mock_publish.assert_called_once_with(appointment=cancelled)


@patch("apps.appointments.services.appointment.publish_appointment_status_notification")
def test_update_appointment_status_publishes_status_notification(mock_publish):
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

    updated = update_appointment_status(
        appointment=appointment,
        actor=provider_user,
        status=AppointmentStatus.COMPLETED,
    )

    mock_publish.assert_called_once_with(appointment=updated)
from apps.offerings.enums import VisitMode

def test_appointment_creates_snapshot_of_visit_mode():
    """Test that appointment successfully records the visit mode of the offering."""
    customer = UserFactory(role=UserRoles.CUSTOMER)
    provider = ProviderProfileFactory()
    
    offering = OfferingFactory(
        provider=provider,
        organization=provider.organization,
        visit_mode=VisitMode.ONLINE_CHAT,  # Explicitly set to online chat
    )

    target_date = date.today() + timedelta(days=7)
    WorkingHourFactory(
        provider=provider,
        weekday=target_date.weekday(),
        start_time=time(9, 0),
        end_time=time(10, 0),
    )
    start_at = make_aware_datetime(target_date, time(9, 0))

    appointment = create_appointment(
        customer=customer,
        provider_id=provider.id,
        offering_id=offering.id,
        start_at=start_at,
    )

    assert appointment.visit_mode == VisitMode.ONLINE_CHAT


def test_appointment_visit_mode_snapshot_is_immutable_when_offering_changes():
    """Test that modifying an offering's visit mode does not affect existing appointments."""
    customer = UserFactory(role=UserRoles.CUSTOMER)
    provider = ProviderProfileFactory()
    
    offering = OfferingFactory(
        provider=provider,
        organization=provider.organization,
        visit_mode=VisitMode.ONLINE_CHAT,
    )

    target_date = date.today() + timedelta(days=7)
    WorkingHourFactory(
        provider=provider,
        weekday=target_date.weekday(),
        start_time=time(9, 0),
        end_time=time(10, 0),
    )
    start_at = make_aware_datetime(target_date, time(9, 0))

    appointment = create_appointment(
        customer=customer,
        provider_id=provider.id,
        offering_id=offering.id,
        start_at=start_at,
    )

    # Change the offering's visit mode after appointment is created
    offering.visit_mode = VisitMode.IN_PERSON
    offering.save()

    # The appointment should retain its original snapshot
    appointment.refresh_from_db()
    assert appointment.visit_mode == VisitMode.ONLINE_CHAT