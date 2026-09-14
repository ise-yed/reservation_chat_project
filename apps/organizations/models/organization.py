from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class Organization(BaseModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_organizations",
    )
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(
        max_length=140,
        unique=True,
        allow_unicode=True,
        db_index=True,
    )
    description = models.TextField(blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    timezone = models.CharField(max_length=64, default="Asia/Tehran")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "organizations"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "-created_at"]),
            models.Index(fields=["is_active", "-created_at"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.name
