# from datetime import date, time, timedelta
# from unittest.mock import patch

# import pytest
# from django.utils import timezone

# from apps.appointments.models import AppointmentReminder
# from apps.appointments.services import (
#     create_appointment,
#     send_due_appointment_24h_reminders,
# )
# from apps.availability.tests.factories import WorkingHourFactory
# from apps.offerings.tests.factories import OfferingFactory
# from apps.providers.tests.factories import ProviderProfileFactory
# from apps.users.enums import UserRoles
# from apps.users.tests.factories import UserFactory

# pytestmark = pytest.mark.django_db


# def make_aware_datetime(target_date, target_time):
#     current_timezone = timezone.get_current_timezone()
#     return timezone.make_aware(
#         timezone.datetime.combine(target_date, target_time),
#         current_timezone,
#     )


# @patch("apps.appointments.services.reminder_service.publish_appointment_reminder_notification")
# def test_due_appointment_24h_reminder_is_sent_once(mock_publish):
#     customer = UserFactory(role=UserRoles.CUSTOMER)
#     provider = ProviderProfileFactory()
#     offering = OfferingFactory(
#         provider=provider,
#         organization=provider.organization,
#         duration_minutes=30,
#     )

#     target_start_at = timezone.now() + timedelta(hours=23, minutes=50)
#     target_date = timezone.localdate(target_start_at)

#     WorkingHourFactory(
#         provider=provider,
#         weekday=target_date.weekday(),
#         start_time=(target_start_at - timedelta(minutes=10)).time(),
#         end_time=(target_start_at + timedelta(hours=1)).time(),
#     )

#     appointment = create_appointment(
#         customer=customer,
#         provider_id=provider.id,
#         offering_id=offering.id,
#         start_at=target_start_at,
#     )

#     first_count = send_due_appointment_24h_reminders()
#     second_count = send_due_appointment_24h_reminders()

#     assert first_count == 1
#     assert second_count == 0
#     assert AppointmentReminder.objects.filter(appointment=appointment).count() == 1
#     mock_publish.assert_called_once_with(appointment=appointment)


# @patch("apps.appointments.services.reminder_service.publish_appointment_reminder_notification")
# def test_appointment_after_more_than_24h_does_not_get_reminder(mock_publish):
#     customer = UserFactory(role=UserRoles.CUSTOMER)
#     provider = ProviderProfileFactory()
#     offering = OfferingFactory(
#         provider=provider,
#         organization=provider.organization,
#         duration_minutes=30,
#     )

#     target_date = date.today() + timedelta(days=7)

#     WorkingHourFactory(
#         provider=provider,
#         weekday=target_date.weekday(),
#         start_time=time(9, 0),
#         end_time=time(10, 0),
#     )

#     create_appointment(
#         customer=customer,
#         provider_id=provider.id,
#         offering_id=offering.id,
#         start_at=make_aware_datetime(target_date, time(9, 0)),
#     )

#     sent_count = send_due_appointment_24h_reminders()

#     assert sent_count == 0
#     mock_publish.assert_not_called()
