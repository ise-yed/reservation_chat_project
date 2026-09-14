from datetime import timedelta

import pytest
from django.utils import timezone

from apps.appointments.tests.factories import AppointmentFactory

pytestmark = pytest.mark.django_db


def test_appointment_str_contains_status():
    start_at = timezone.now() + timedelta(days=1)
    end_at = start_at + timedelta(minutes=30)

    appointment = AppointmentFactory(
        start_at=start_at,
        end_at=end_at,
        blocked_start_at=start_at,
        blocked_end_at=end_at,
    )

    assert appointment.status in str(appointment)
