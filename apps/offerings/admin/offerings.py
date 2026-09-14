from django.contrib import admin

from apps.offerings.models import Offering


@admin.register(Offering)
class OfferingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "organization",
        "provider",
        "duration_minutes",
        "price",
        "requires_approval",
        "is_active",
        "created_at",
    )
    list_filter = (
        "is_active",
        "requires_approval",
        "organization",
        "provider",
        "created_at",
    )
    search_fields = (
        "title",
        "description",
        "organization__name",
        "provider__user__email",
        "provider__user__first_name",
        "provider__user__last_name",
        "provider__specialty",
    )
    readonly_fields = ("id", "created_at", "updated_at")
