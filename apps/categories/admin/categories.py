from django.contrib import admin
from django.core.cache import cache

from apps.categories.models import Category

CATEGORY_LIST_CACHE_KEY = "categories:active:list"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # فیلدهای icon و parent از اینجا حذف شدند
    list_display = ("id", "name", "slug", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "description", "slug")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("id", "created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        cache.delete(CATEGORY_LIST_CACHE_KEY)

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        cache.delete(CATEGORY_LIST_CACHE_KEY)

    def delete_queryset(self, request, queryset):
        super().delete_queryset(request, queryset)
        cache.delete(CATEGORY_LIST_CACHE_KEY)
