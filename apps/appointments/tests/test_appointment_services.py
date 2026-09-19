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
from apps.offerings.enums import VisitMode
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


def test_customer_can_create_appointment_and_conversation_links():
    """Test ONLINE_CHAT appointment creation creates/links a conversation."""
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
        visit_mode=VisitMode.ONLINE_CHAT,  # اضافه‌شده برای اجرای منطق ساخت چت
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

    assert appointment.status == AppointmentStatus.CONFIRMED
    assert appointment.conversation is not None
    assert appointment.conversation.customer == customer
    assert appointment.conversation.provider == provider.user


def test_multiple_appointments_reuse_same_conversation():
    """Test that two appointments between the same pair reuse the same conversation."""
    customer = UserFactory(role=UserRoles.CUSTOMER)
    provider_user = UserFactory(role=UserRoles.PROVIDER)
    provider = ProviderProfileFactory(user=provider_user)

    offering = OfferingFactory(
        provider=provider,
        organization=provider.organization,
        duration_minutes=30,
        buffer_before_minutes=0,
        buffer_after_minutes=0,
        visit_mode=VisitMode.ONLINE_CHAT,  # اضافه‌شده
    )

    target_date = date.today() + timedelta(days=7)

    WorkingHourFactory(
        provider=provider,
        weekday=target_date.weekday(),
        start_time=time(9, 0),
        end_time=time(12, 0),
    )

    # نوبت اول
    app1 = create_appointment(
        customer=customer,
        provider_id=provider.id,
        offering_id=offering.id,
        start_at=make_aware_datetime(target_date, time(9, 0)),
    )

    # نوبت دوم برای همان بیمار و پزشک
    app2 = create_appointment(
        customer=customer,
        provider_id=provider.id,
        offering_id=offering.id,
        start_at=make_aware_datetime(target_date, time(10, 0)),
    )

    assert app1.id != app2.id
    assert app1.conversation is not None
    assert app2.conversation is not None
    # باید دقیقاً از یک چتِ مشترک استفاده کنند
    assert app1.conversation == app2.conversation
    assert app1.conversation.customer == customer
    assert app1.conversation.provider == provider.user


def test_in_person_appointment_does_not_create_conversation():
    """Test IN_PERSON appointment does NOT create or link a conversation."""
    customer = UserFactory(role=UserRoles.CUSTOMER)
    provider = ProviderProfileFactory()

    offering = OfferingFactory(
        provider=provider,
        organization=provider.organization,
        requires_approval=False,
        visit_mode=VisitMode.IN_PERSON,  # نوبت حضوری
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

    assert appointment.status == AppointmentStatus.CONFIRMED
    assert appointment.conversation is None  # بدون ارتباط چت


def test_appointment_requires_pending_status_creates_conversation_on_confirm():
    """Test PENDING appointment gets conversation ONLY when updated to CONFIRMED."""
    customer = UserFactory(role=UserRoles.CUSTOMER)
    provider_user = UserFactory(role=UserRoles.PROVIDER)
    provider = ProviderProfileFactory(user=provider_user)

    offering = OfferingFactory(
        provider=provider,
        organization=provider.organization,
        requires_approval=True,  # نیاز به تایید دارد
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

    assert appointment.status == AppointmentStatus.PENDING
    assert appointment.conversation is None  # در حالت تعلیق ساخته نمی‌شود

    updated = update_appointment_status(
        appointment=appointment,
        actor=provider_user,
        status=AppointmentStatus.CONFIRMED,
    )

    assert updated.status == AppointmentStatus.CONFIRMED
    assert updated.conversation is not None  # پس از تایید ساخته شد


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
        visit_mode=VisitMode.ONLINE_CHAT,  # اضافه‌شده
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
    assert first.conversation is not None
    assert second.conversation is not None
    # این دو نوبت برای دو بیمارِ متفاوت هستند، پس باید دو چت متفاوت داشته باشند
    assert first.conversation != second.conversation


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
    """Test completing appointment sets status and completed_at."""
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

    assert appointment.completed_at is None

    updated = update_appointment_status(
        appointment=appointment,
        actor=provider_user,
        status=AppointmentStatus.COMPLETED,
    )

    assert updated.status == AppointmentStatus.COMPLETED
    assert updated.completed_at is not None  # زمان پایان ست شد


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


def test_appointment_creates_snapshot_of_visit_mode():
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

    assert appointment.visit_mode == VisitMode.ONLINE_CHAT


def test_appointment_visit_mode_snapshot_is_immutable_when_offering_changes():
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

    offering.visit_mode = VisitMode.IN_PERSON
    offering.save()

    appointment.refresh_from_db()
    assert appointment.visit_mode == VisitMode.ONLINE_CHAT
