from django.db import models

from apps.common.models import BaseModel


class Weekday(models.IntegerChoices):
    MONDAY = 0, "Monday"
    TUESDAY = 1, "Tuesday"
    WEDNESDAY = 2, "Wednesday"
    THURSDAY = 3, "Thursday"
    FRIDAY = 4, "Friday"
    SATURDAY = 5, "Saturday"
    SUNDAY = 6, "Sunday"


class WorkingHour(BaseModel):
    provider = models.ForeignKey(
        "providers.ProviderProfile",
        on_delete=models.CASCADE,
        related_name="working_hours",
    )
    weekday = models.PositiveSmallIntegerField(
        choices=Weekday.choices,
        db_index=True,
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "provider_working_hours"
        ordering = ["weekday", "start_time"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F("start_time")),
                name="working_hour_end_time_after_start_time",
            ),
        ]
        indexes = [
            models.Index(fields=["provider", "weekday", "is_active"]),
            models.Index(fields=["weekday", "start_time", "end_time"]),
        ]

    def __str__(self):
        return f"{self.provider} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"


class TimeOff(BaseModel):
    provider = models.ForeignKey(
        "providers.ProviderProfile",
        on_delete=models.CASCADE,
        related_name="time_offs",
    )
    start_at = models.DateTimeField(db_index=True)
    end_at = models.DateTimeField(db_index=True)
    reason = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "provider_time_offs"
        ordering = ["-start_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_at__gt=models.F("start_at")),
                name="time_off_end_at_after_start_at",
            ),
        ]
        indexes = [
            models.Index(fields=["provider", "start_at", "end_at"]),
            models.Index(fields=["provider", "is_active"]),
        ]

    def __str__(self):
        return f"{self.provider} - {self.start_at} to {self.end_at}"


class Holiday(BaseModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="holidays",
    )
    date = models.DateField(db_index=True)
    title = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "organization_holidays"
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "date"],
                name="unique_holiday_date_per_organization",
            )
        ]
        indexes = [
            models.Index(fields=["organization", "date", "is_active"]),
        ]

    def __str__(self):
        return f"{self.organization.name} - {self.date} - {self.title}"
