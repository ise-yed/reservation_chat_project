
from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class FCMDevice(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fcm_devices",
    )
    registration_id = models.CharField(max_length=255, unique=True)
    device_type = models.CharField(
        max_length=20,
        choices=[("android", "Android"), ("ios", "iOS"), ("web", "Web")],
        default="android"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"{self.device_type} - {self.user}"
