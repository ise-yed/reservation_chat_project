from django.db import models


class NotificationType(models.TextChoices):
    PASSWORD_CHANGED = "password_changed", "Password Changed"
    PASSWORD_RESET_REQUESTED = "password_reset_requested", "Password Reset Requested"

    APPOINTMENT_CREATED = "appointment_created", "Appointment Created"
    APPOINTMENT_CONFIRMED = "appointment_confirmed", "Appointment Confirmed"
    APPOINTMENT_CANCELLED = "appointment_cancelled", "Appointment Cancelled"
    APPOINTMENT_RESCHEDULED = "appointment_rescheduled", "Appointment Rescheduled"
    APPOINTMENT_REMINDER = "appointment_reminder", "Appointment Reminder"
    APPOINTMENT_COMPLETED = "appointment_completed", "Appointment Completed"
    APPOINTMENT_NO_SHOW = "appointment_no_show", "Appointment No Show"

    PAYMENT_SUCCESS = "payment_success", "Payment Success"
    PAYMENT_FAILED = "payment_failed", "Payment Failed"
    REFUND_SUCCESS = "refund_success", "Refund Success"


class NotificationChannel(models.TextChoices):
    IN_APP = "in_app", "In App"
    EMAIL = "email", "Email"
    SMS = "sms", "SMS"
    PUSH = "push", "Push"


class NotificationDeliveryStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    SKIPPED = "skipped", "Skipped"
