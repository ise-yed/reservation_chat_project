from django.contrib import admin

from apps.payments.enums import PaymentStatus
from apps.payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "appointment", "amount", "method", "status", "paid_at", "created_at")
    list_filter = ("status", "method", "created_at")
    search_fields = ("appointment__customer__email", "appointment__offering__title", "gateway_reference")
    readonly_fields = ("id", "created_at", "updated_at", "paid_at")
    actions = ["mark_refunded"]

    @admin.action(description="Mark selected paid payments as refunded")
    def mark_refunded(self, request, queryset):
        updated = queryset.filter(status=PaymentStatus.PAID).update(status=PaymentStatus.REFUNDED)
        self.message_user(request, f"{updated} payment(s) marked as refunded.")
