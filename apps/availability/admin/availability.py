from django.contrib import admin

from apps.availability.models import Holiday, TimeOff, WorkingHour


@admin.register(WorkingHour)
class WorkingHourAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "provider",
        "weekday",
        "start_time",
        "end_time",
        "is_active",
        "created_at",
    )
    list_filter = ("weekday", "is_active", "created_at")
    search_fields = (
        "provider__user__email",
        "provider__user__first_name",
        "provider__user__last_name",
        "provider__organization__name",
        "provider__specialty",
    )
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(TimeOff)
class TimeOffAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "provider",
        "start_at",
        "end_at",
        "reason",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "start_at", "created_at")
    search_fields = (
        "provider__user__email",
        "provider__user__first_name",
        "provider__user__last_name",
        "provider__organization__name",
        "reason",
    )
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "organization",
        "date",
        "title",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "date", "created_at")
    search_fields = ("organization__name", "title")
    readonly_fields = ("id", "created_at", "updated_at")
