from celery import shared_task

from apps.appointments.services import (
    expire_unpaid_appointments,
    send_due_appointment_24h_reminders,
)


@shared_task
def send_due_appointment_24h_reminders_task() -> int:
    return send_due_appointment_24h_reminders()


@shared_task
def expire_unpaid_appointments_task() -> int:
    return expire_unpaid_appointments()
