import pytest

from apps.availability.tests.factories import (
    HolidayFactory,
    TimeOffFactory,
    WorkingHourFactory,
)

pytestmark = pytest.mark.django_db


def test_working_hour_str_contains_provider():
    working_hour = WorkingHourFactory()

    assert str(working_hour.provider) in str(working_hour)


def test_time_off_str_contains_provider():
    time_off = TimeOffFactory()

    assert str(time_off.provider) in str(time_off)


def test_holiday_str_contains_title():
    holiday = HolidayFactory(title="Nowruz")

    assert "Nowruz" in str(holiday)
