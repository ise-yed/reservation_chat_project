from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class ProviderProfile(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="provider_profiles",
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="providers",
    )
    branch = models.ForeignKey(
        "organizations.Branch",
        on_delete=models.SET_NULL,
        related_name="providers",
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=150, blank=True)
    specialty = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)

    default_slot_duration_minutes = models.PositiveSmallIntegerField(default=30)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "provider_profiles"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "organization"],
                name="unique_provider_profile_per_user_organization",
            )
        ]
        indexes = [
            models.Index(fields=["organization", "is_active"]),
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["branch", "is_active"]),
            models.Index(fields=["specialty"]),
        ]

    def __str__(self):
        full_name = self.user.full_name or self.user.email
        if self.specialty:
            return f"{full_name} - {self.specialty}"
        return full_name
