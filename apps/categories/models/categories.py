from django.db import models
from django.utils.text import slugify

from apps.common.models import BaseModel


class Category(BaseModel):
    """Model for categorizing offerings and other entities."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="FontAwesome or custom icon class")
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#4F46E5", help_text="Hex color code")

    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children"
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "categories"
        ordering = ["name"]
        verbose_name_plural = "Categories"
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
