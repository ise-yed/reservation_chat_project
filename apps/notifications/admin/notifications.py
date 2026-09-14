from django.contrib import admin

from apps.notifications.models import Notification, NotificationDelivery


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "type",
        "title",
        "is_read",
        "created_at",
    )
    list_filter = (
        "type",
        "is_read",
        "created_at",
    )
    search_fields = (
        "title",
        "message",
        "user__email",
        "user__phone_number",
    )
    readonly_fields = (
        "created_at",
        "read_at",
    )
    ordering = ("-created_at",)


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "channel",
        "type",
        "recipient",
        "status",
        "user",
        "sent_at",
        "created_at",
    )
    list_filter = (
        "channel",
        "type",
        "status",
        "created_at",
        "sent_at",
    )
    search_fields = (
        "recipient",
        "subject",
        "body",
        "user__email",
        "error_message",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "sent_at",
    )
    ordering = ("-created_at",)
