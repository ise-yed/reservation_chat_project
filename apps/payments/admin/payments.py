from django.contrib import admin

from apps.payments.models import Payment, PaymentTransaction


class PaymentTransactionInline(admin.TabularInline):
    model = PaymentTransaction
    extra = 0
    readonly_fields = (
        "id",
        "transaction_type",
        "amount",
        "status",
        "gateway_reference",
        "message",
        "raw_response",
        "created_at",
        "updated_at",
    )
    can_delete = False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "appointment",
        "payer",
        "organization",
        "amount",
        "currency",
        "status",
        "method",
        "paid_at",
        "created_at",
    )
    list_filter = (
        "status",
        "method",
        "currency",
        "organization",
        "created_at",
        "paid_at",
    )
    search_fields = (
        "payer__email",
        "payer__first_name",
        "payer__last_name",
        "organization__name",
        "appointment__offering__title",
        "gateway_reference",
        "idempotency_key",
    )
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "paid_at",
        "failed_at",
        "cancelled_at",
        "refunded_at",
    )
    inlines = [PaymentTransactionInline]


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "payment",
        "transaction_type",
        "amount",
        "status",
        "gateway_reference",
        "created_at",
    )
    list_filter = ("transaction_type", "status", "created_at")
    search_fields = (
        "payment__payer__email",
        "payment__appointment__offering__title",
        "gateway_reference",
        "message",
    )
    readonly_fields = ("id", "created_at", "updated_at")
