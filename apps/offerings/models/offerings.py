from django.db import models

from apps.common.models import BaseModel
from apps.offerings.enums import VisitMode


class Offering(BaseModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="offerings",
    )
    provider = models.ForeignKey(
        "providers.ProviderProfile",
        on_delete=models.PROTECT,
        related_name="offerings",
    )
    specialty = models.ForeignKey(
        "categories.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="offerings",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    visit_mode = models.CharField(
        max_length=32,
        choices=VisitMode.choices,
        default=VisitMode.IN_PERSON,
        db_index=True,
    )

    duration_minutes = models.PositiveSmallIntegerField(default=30)
    buffer_before_minutes = models.PositiveSmallIntegerField(default=0)
    buffer_after_minutes = models.PositiveSmallIntegerField(default=0)

    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    requires_approval = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "offerings"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "title"],
                name="unique_offering_title_per_provider",
            )
        ]
        indexes = [
            models.Index(fields=["organization", "is_active"]),
            models.Index(fields=["provider", "is_active"]),
            models.Index(fields=["title"]),
            models.Index(fields=["price"]),
            models.Index(fields=["specialty"]),
            models.Index(fields=["visit_mode"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.provider}"
