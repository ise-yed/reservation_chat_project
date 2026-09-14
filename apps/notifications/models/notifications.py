import json
import uuid

from django.conf import settings
from django.db import models

from apps.common.models import BaseModel
from apps.notifications.enums import (
    NotificationChannel,
    NotificationDeliveryStatus,
    NotificationType,
)


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if hasattr(obj, "pk"):
            return str(obj.pk)
        return super().default(obj)


class Notification(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    type = models.CharField(
        max_length=80,
        choices=NotificationType.choices,
    )

    title = models.CharField(max_length=255)
    message = models.TextField()

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    related_object_type = models.CharField(max_length=100, blank=True)
    related_object_id = models.CharField(max_length=64, null=True, blank=True)
    data = models.JSONField(default=dict, encoder=UUIDEncoder)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user", "is_read", "-created_at"]),
            models.Index(fields=["related_object_type", "related_object_id"]),
            models.Index(fields=["type", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.title}"


class NotificationDelivery(BaseModel):
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="deliveries",
        null=True,
        blank=True,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="notification_deliveries",
        null=True,
        blank=True,
    )

    channel = models.CharField(
        max_length=30,
        choices=NotificationChannel.choices,
    )

    type = models.CharField(
        max_length=80,
        choices=NotificationType.choices,
    )

    recipient = models.CharField(max_length=255)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)

    status = models.CharField(
        max_length=30,
        choices=NotificationDeliveryStatus.choices,
        default=NotificationDeliveryStatus.PENDING,
    )

    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    data = models.JSONField(default=dict, blank=True, encoder=UUIDEncoder)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["channel", "status", "-created_at"]),
            models.Index(fields=["type", "-created_at"]),
            models.Index(fields=["recipient", "-created_at"]),
            models.Index(fields=["notification", "channel"]),
        ]

    def __str__(self):
        return f"{self.channel} - {self.recipient} - {self.status}"
