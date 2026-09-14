from datetime import date, time, timedelta

import pytest
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.availability.models import Weekday
from apps.availability.services import (
    create_holiday,
    create_time_off,
    create_working_hour,
    get_available_slots,
)
from apps.availability.tests.factories import WorkingHourFactory
from apps.offerings.tests.factories import OfferingFactory
from apps.organizations.tests.factories import OrganizationFactory
from apps.providers.tests.factories import ProviderProfileFactory
from apps.users.enums import UserRoles
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_provider_user_can_create_own_working_hour():
    provider_user = UserFactory(role=UserRoles.PROVIDER)
    provider = ProviderProfileFactory(user=provider_user)

    working_hour = create_working_hour(
        actor=provider_user,
        provider_id=provider.id,
        weekday=Weekday.MONDAY,
        start_time=time(9, 0),
        end_time=time(12, 0),
    )

    assert working_hour.provider == provider
    assert working_hour.weekday == Weekday.MONDAY


def test_non_manager_cannot_create_working_hour():
    other_user = UserFactory(role=UserRoles.PROVIDER)
    provider = ProviderProfileFactory()

    with pytest.raises(PermissionDenied):
        create_working_hour(
            actor=other_user,
            provider_id=provider.id,
            weekday=Weekday.MONDAY,
            start_time=time(9, 0),
            end_time=time(12, 0),
        )


def test_overlapping_working_hour_is_not_allowed():
    provider_user = UserFactory(role=UserRoles.PROVIDER)
    provider = ProviderProfileFactory(user=provider_user)

    create_working_hour(
        actor=provider_user,
        provider_id=provider.id,
        weekday=Weekday.MONDAY,
        start_time=time(9, 0),
        end_time=time(12, 0),
    )

    with pytest.raises(ValidationError):
        create_working_hour(
            actor=provider_user,
            provider_id=provider.id,
            weekday=Weekday.MONDAY,
            start_time=time(11, 0),
            end_time=time(13, 0),
        )


def test_provider_user_can_create_time_off():
    provider_user = UserFactory(role=UserRoles.PROVIDER)
    provider = ProviderProfileFactory(user=provider_user)

    start_at = timezone.now() + timedelta(days=1)
    end_at = start_at + timedelta(hours=2)

    time_off = create_time_off(
        actor=provider_user,
        provider_id=provider.id,
        start_at=start_at,
        end_at=end_at,
        reason="Personal",
    )

    assert time_off.provider == provider
    assert time_off.reason == "Personal"


def test_organization_owner_can_create_holiday():
    owner = UserFactory(role=UserRoles.PROVIDER)
    organization = OrganizationFactory(owner=owner)

    holiday = create_holiday(
        actor=owner,
        organization_id=organization.id,
        date=date.today() + timedelta(days=1),
        title="Holiday",
    )

    assert holiday.organization == organization
    assert holiday.title == "Holiday"


def test_available_slots_are_generated_from_working_hours():
    provider_user = UserFactory(role=UserRoles.PROVIDER)
    provider = ProviderProfileFactory(user=provider_user)
    offering = OfferingFactory(
        provider=provider,
        organization=provider.organization,
        duration_minutes=30,
        buffer_before_minutes=0,
        buffer_after_minutes=0,
        is_active=True,
    )

    target_date = date.today() + timedelta(days=7)
    weekday = target_date.weekday()

    WorkingHourFactory(
        provider=provider,
        weekday=weekday,
        start_time=time(9, 0),
        end_time=time(10, 0),
        is_active=True,
    )

    slots = get_available_slots(
        provider_id=provider.id,
        offering_id=offering.id,
        target_date=target_date,
    )

    assert len(slots) == 2
    assert slots[0]["duration_minutes"] == 30


def test_holiday_removes_all_slots():
    owner = UserFactory(role=UserRoles.PROVIDER)
    organization = OrganizationFactory(owner=owner)
    provider = ProviderProfileFactory(user=owner, organization=organization)
    offering = OfferingFactory(
        provider=provider,
        organization=organization,
        duration_minutes=30,
    )

    target_date = date.today() + timedelta(days=7)

    WorkingHourFactory(
        provider=provider,
        weekday=target_date.weekday(),
        start_time=time(9, 0),
        end_time=time(10, 0),
    )

    create_holiday(
        actor=owner,
        organization_id=organization.id,
        date=target_date,
        title="Closed",
    )

    slots = get_available_slots(
        provider_id=provider.id,
        offering_id=offering.id,
        target_date=target_date,
    )

    assert slots == []
