from django.conf import settings
from django.db import models

from apps.common.models import BaseModel
from apps.payments.enums import (
    PaymentMethod,
    PaymentStatus,
    PaymentTransactionType,
)


class Payment(BaseModel):
    appointment = models.ForeignKey(
        "appointments.Appointment",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="IRR")

    status = models.CharField(
        max_length=30,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
    )
    method = models.CharField(
        max_length=40,
        choices=PaymentMethod.choices,
        default=PaymentMethod.MOCK,
    )

    gateway_reference = models.CharField(max_length=255, blank=True)
    idempotency_key = models.CharField(max_length=255, unique=True)

    paid_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)

    failure_reason = models.TextField(blank=True)
    refund_reason = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_payments",
    )

    data = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["appointment", "status"]),
            models.Index(fields=["organization", "status", "-created_at"]),
            models.Index(fields=["payer", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["gateway_reference"]),
        ]

    def __str__(self):
        return f"{self.appointment_id} - {self.amount} - {self.status}"


class PaymentTransaction(BaseModel):
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    transaction_type = models.CharField(
        max_length=30,
        choices=PaymentTransactionType.choices,
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=30, default="success")
    gateway_reference = models.CharField(max_length=255, blank=True)
    message = models.TextField(blank=True)
    raw_response = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "payment_transactions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["payment", "-created_at"]),
            models.Index(fields=["transaction_type", "-created_at"]),
            models.Index(fields=["gateway_reference"]),
        ]

    def __str__(self):
        return f"{self.payment_id} - {self.transaction_type} - {self.amount}"
