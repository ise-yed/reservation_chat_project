from django.conf import settings
from django.db import models

from apps.audit.enums import AuditAction, AuditStatus
from apps.common.models import BaseModel


class AuditLog(BaseModel):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        null=True,
        blank=True,
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        null=True,
        blank=True,
    )

    action = models.CharField(
        max_length=80,
        choices=AuditAction.choices,
        db_index=True,
    )
    status = models.CharField(
        max_length=30,
        choices=AuditStatus.choices,
        default=AuditStatus.SUCCESS,
        db_index=True,
    )

    target_object_type = models.CharField(max_length=100, db_index=True)
    target_object_id = models.CharField(max_length=64, blank=True, db_index=True)
    target_object_repr = models.CharField(max_length=255, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["actor", "-created_at"]),
            models.Index(fields=["organization", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["target_object_type", "target_object_id"]),
        ]

    def __str__(self):
        return f"{self.action} - {self.target_object_type}:{self.target_object_id}"
