from django.db import models


class AppointmentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    CANCELLED_BY_CUSTOMER = "cancelled_by_customer", "Cancelled by customer"
    CANCELLED_BY_PROVIDER = "cancelled_by_provider", "Cancelled by provider"
    COMPLETED = "completed", "Completed"
    NO_SHOW = "no_show", "No show"


ACTIVE_APPOINTMENT_STATUSES = [
    AppointmentStatus.PENDING,
    AppointmentStatus.CONFIRMED,
]

CANCELLABLE_APPOINTMENT_STATUSES = [
    AppointmentStatus.PENDING,
    AppointmentStatus.CONFIRMED,
]

FINAL_APPOINTMENT_STATUSES = [
    AppointmentStatus.CANCELLED_BY_CUSTOMER,
    AppointmentStatus.CANCELLED_BY_PROVIDER,
    AppointmentStatus.COMPLETED,
    AppointmentStatus.NO_SHOW,
]


class AppointmentReminderType(models.TextChoices):
    REMINDER_24H = "reminder_24h", "Reminder 24 hours before appointment"
