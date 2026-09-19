from django.contrib import admin

from apps.chat.models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "provider", "created_at", "updated_at")
    search_fields = (
        "id",
        "customer__phone_number",
        "customer__first_name",
        "customer__last_name",
        "provider__phone_number"
    )
    list_filter = ("created_at",)
    readonly_fields = ("id", "created_at", "updated_at", "patient_last_read_message", "doctor_last_read_message")
    ordering = ("-updated_at",)
    raw_id_fields = ("customer", "provider", "last_message")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "type", "is_deleted", "created_at")
    search_fields = ("id", "conversation__id", "sender__phone_number")
    list_filter = ("type", "is_deleted", "created_at")

    # فیلدهای حساس و سیستمی نباید توسط ادمین به صورت دستی تغییر کنند
    readonly_fields = ("id", "created_at", "deleted_at", "deleted_by", "file_name", "file_size", "mime_type")
    ordering = ("-created_at",)
    raw_id_fields = ("conversation", "sender")

    def get_readonly_fields(self, request, obj=None):
        """اگر پیام از قبل ثبت شده باشد، امکان ویرایش متن و فایل آن را در ادمین می‌بندیم (امنیت پزشکی)"""
        if obj:
            return self.readonly_fields + ("content", "attachment", "type")
        return self.readonly_fields
