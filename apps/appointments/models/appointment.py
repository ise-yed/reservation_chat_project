from django.conf import settings
from django.db import models

from apps.appointments.enums import AppointmentStatus
from apps.common.models import BaseModel
from apps.offerings.enums import VisitMode


class Appointment(BaseModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="appointments",
    )
    branch = models.ForeignKey(
        "organizations.Branch",
        on_delete=models.PROTECT,
        related_name="appointments",
        null=True,
        blank=True,
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="customer_appointments",
    )
    provider = models.ForeignKey(
        "providers.ProviderProfile",
        on_delete=models.PROTECT,
        related_name="appointments",
    )
    offering = models.ForeignKey(
        "offerings.Offering",
        on_delete=models.PROTECT,
        related_name="appointments",
    )

    visit_mode = models.CharField(
        max_length=32,
        choices=VisitMode.choices,
        db_index=True,
    )

    start_at = models.DateTimeField(db_index=True)
    end_at = models.DateTimeField(db_index=True)

    blocked_start_at = models.DateTimeField(db_index=True)
    blocked_end_at = models.DateTimeField(db_index=True)

    status = models.CharField(
        max_length=32,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.CONFIRMED,
        db_index=True,
    )

    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    notes = models.TextField(blank=True)

    cancel_reason = models.TextField(blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="cancelled_appointments",
        null=True,
        blank=True,
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_appointments",
    )

    class Meta:
        db_table = "appointments"
        ordering = ["-start_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_at__gt=models.F("start_at")),
                name="appointment_end_at_after_start_at",
            ),
            models.CheckConstraint(
                condition=models.Q(blocked_end_at__gt=models.F("blocked_start_at")),
                name="appointment_blocked_end_after_blocked_start",
            ),
        ]
        indexes = [
            models.Index(fields=["customer", "start_at"]),
            models.Index(fields=["provider", "start_at", "end_at"]),
            models.Index(fields=["provider", "blocked_start_at", "blocked_end_at"]),
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["status", "start_at"]),
            models.Index(fields=["visit_mode"]),
        ]

    def __str__(self):
        return f"{self.provider} - {self.start_at} - {self.status}"
