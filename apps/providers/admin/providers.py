from django.contrib import admin

from apps.providers.models import ProviderProfile


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    """Admin interface for managing Provider Profiles."""

    list_display = (
        "id",
        "user",
        "organization",
        "branch",
        "get_specialties",
        "bio",
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
        "specialties__name",
    )
    readonly_fields = ("id", "created_at", "updated_at")
    filter_horizontal = ("specialties",)

    def get_queryset(self, request):
        """
        Optimize database queries to prevent the N+1 problem.
        Uses select_related for ForeignKeys and prefetch_related for ManyToManyFields.
        """
        qs = super().get_queryset(request)
        return qs.select_related("user", "organization", "branch").prefetch_related("specialties")

    def get_specialties(self, obj):
        """Return a comma-separated string of specialty names for the list view."""
        return ", ".join([specialty.name for specialty in obj.specialties.all()])

    get_specialties.short_description = "Specialties"
