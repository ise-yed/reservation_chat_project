from django.contrib import admin

from apps.organizations.models import Branch, Organization


class BranchInline(admin.TabularInline):
    model = Branch
    extra = 0
    fields = (
        "name",
        "phone_number",
        "address",
        "latitude",
        "longitude",
        "is_active",
    )


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "slug",
        "owner",
        "phone_number",
        "email",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "created_at")
    search_fields = (
        "name",
        "slug",
        "owner__email",
        "phone_number",
        "email",
    )
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [BranchInline]


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "organization",
        "phone_number",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "created_at")
    search_fields = (
        "name",
        "organization__name",
        "phone_number",
        "address",
    )
    readonly_fields = ("id", "created_at", "updated_at")
