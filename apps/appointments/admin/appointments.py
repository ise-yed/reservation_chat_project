from django.contrib import admin

from apps.appointments.models import Appointment, AppointmentReminder


@admin.register(AppointmentReminder)
class AppointmentReminderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "appointment",
        "reminder_type",
        "channel",
        "sent_at",
        "created_at",
    )
    list_filter = (
        "reminder_type",
        "channel",
        "sent_at",
        "created_at",
    )
    search_fields = (
        "appointment__customer__email",
        "appointment__provider__user__email",
        "appointment__offering__title",
    )
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer",
        "provider",
        "offering",
        "start_at",
        "end_at",
        "status",
        "price",
        "created_at",
    )
    list_filter = (
        "status",
        "organization",
        "provider",
        "start_at",
        "created_at",
    )
    search_fields = (
        "customer__email",
        "customer__first_name",
        "customer__last_name",
        "provider__user__email",
        "provider__user__first_name",
        "provider__user__last_name",
        "offering__title",
        "organization__name",
    )
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )
