from django.contrib import admin

from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "actor",
        "organization",
        "action",
        "status",
        "target_object_type",
        "target_object_id",
        "created_at",
    )
    list_filter = (
        "action",
        "status",
        "organization",
        "created_at",
    )
    search_fields = (
        "actor__email",
        "actor__first_name",
        "actor__last_name",
        "organization__name",
        "target_object_type",
        "target_object_id",
        "target_object_repr",
        "error_message",
    )
    readonly_fields = (
        "id",
        "actor",
        "organization",
        "action",
        "status",
        "target_object_type",
        "target_object_id",
        "target_object_repr",
        "ip_address",
        "user_agent",
        "metadata",
        "error_message",
        "created_at",
        "updated_at",
    )
