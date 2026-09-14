from django.contrib import admin

from apps.providers.models import ProviderProfile


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "organization",
        "branch",
        "specialty",
        "default_slot_duration_minutes",
        "is_active",
        "created_at",
    )
    list_filter = (
        "is_active",
        "organization",
        "branch",
        "created_at",
    )
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "organization__name",
        "branch__name",
        "title",
        "specialty",
    )
    readonly_fields = ("id", "created_at", "updated_at")
