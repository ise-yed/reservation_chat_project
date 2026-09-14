from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.appointments.enums import (
    ACTIVE_APPOINTMENT_STATUSES,
    AppointmentReminderType,
)
from apps.appointments.models import Appointment, AppointmentReminder
from apps.appointments.services.notification import (
    publish_appointment_reminder_notification,
)
from apps.notifications.enums import NotificationChannel

REMINDER_24H_DELTA = timedelta(hours=24)


def get_due_24h_reminder_appointments(*, now=None):
    now = now or timezone.now()

    reminder_due_until = now + REMINDER_24H_DELTA

    return (
        Appointment.objects.filter(
            status__in=ACTIVE_APPOINTMENT_STATUSES,
            start_at__gt=now,
            start_at__lte=reminder_due_until,
        )
        .exclude(
            reminders__reminder_type=AppointmentReminderType.REMINDER_24H,
            reminders__channel=NotificationChannel.EMAIL,
        )
        .select_related(
            "organization",
            "branch",
            "customer",
            "provider",
            "provider__user",
            "offering",
        )
        .order_by("start_at")
    )


@transaction.atomic
def send_appointment_24h_reminder(*, appointment) -> bool:
    try:
        AppointmentReminder.objects.create(
            appointment=appointment,
            reminder_type=AppointmentReminderType.REMINDER_24H,
            channel=NotificationChannel.EMAIL,
            sent_at=timezone.now(),
        )
    except IntegrityError:
        return False

    publish_appointment_reminder_notification(appointment=appointment)

    return True


def send_due_appointment_24h_reminders(*, now=None, limit: int = 100) -> int:
    sent_count = 0

    appointments = get_due_24h_reminder_appointments(now=now)[:limit]

    for appointment in appointments:
        was_sent = send_appointment_24h_reminder(appointment=appointment)
        if was_sent:
            sent_count += 1

    return sent_count
