from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("-created_at",)
    list_display = (
        "id",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_staff",
        "is_active",
        "is_verified",
        "created_at",
    )
    search_fields = ("email", "first_name", "last_name", "phone_number")
    readonly_fields = ("created_at", "updated_at", "last_login")

    fieldsets = (
        ("Authentication", {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone_number", "role")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_verified",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_active", "role"),
            },
        ),
    )

    filter_horizontal = ("groups", "user_permissions")
