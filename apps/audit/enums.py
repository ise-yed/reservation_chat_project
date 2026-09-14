from django.db import models


class AuditAction(models.TextChoices):
    APPOINTMENT_CREATED = "appointment_created", "Appointment Created"
    APPOINTMENT_CANCELLED = "appointment_cancelled", "Appointment Cancelled"
    APPOINTMENT_STATUS_CHANGED = "appointment_status_changed", "Appointment Status Changed"

    PAYMENT_INITIATED = "payment_initiated", "Payment Initiated"
    PAYMENT_PAID = "payment_paid", "Payment Paid"
    PAYMENT_FAILED = "payment_failed", "Payment Failed"
    PAYMENT_CANCELLED = "payment_cancelled", "Payment Cancelled"
    PAYMENT_REFUNDED = "payment_refunded", "Payment Refunded"

    WORKING_HOUR_CREATED = "working_hour_created", "Working Hour Created"
    WORKING_HOUR_UPDATED = "working_hour_updated", "Working Hour Updated"
    TIME_OFF_CREATED = "time_off_created", "Time Off Created"
    TIME_OFF_UPDATED = "time_off_updated", "Time Off Updated"
    HOLIDAY_CREATED = "holiday_created", "Holiday Created"
    HOLIDAY_UPDATED = "holiday_updated", "Holiday Updated"


class AuditStatus(models.TextChoices):
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"


class AuditObjectType(models.TextChoices):
    APPOINTMENT = "appointment", "Appointment"
    PAYMENT = "payment", "Payment"
    PROVIDER = "provider", "Provider"
    ORGANIZATION = "organization", "Organization"
    OFFERING = "offering", "Offering"
