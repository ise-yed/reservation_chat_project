from django.db import models

from apps.appointments.enums import AppointmentReminderType
from apps.common.models import BaseModel


class AppointmentReminder(BaseModel):
    appointment = models.ForeignKey(
        "appointments.Appointment",
        on_delete=models.CASCADE,
        related_name="reminders",
    )
    reminder_type = models.CharField(
        max_length=40,
        choices=AppointmentReminderType.choices,
    )
    channel = models.CharField(max_length=30)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "appointment_reminders"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["appointment", "reminder_type", "channel"],
                name="unique_appointment_reminder_per_channel",
            )
        ]
        indexes = [
            models.Index(fields=["channel", "sent_at"]),
        ]

    def __str__(self):
        return f"{self.appointment_id} - {self.reminder_type} - {self.channel}"
