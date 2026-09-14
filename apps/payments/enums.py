from django.db import models


class PaymentStatus(models.TextChoices):
    """Payment status choices."""

    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"
    REFUNDED = "refunded", "Refunded"


class PaymentMethod(models.TextChoices):
    """Payment method choices."""

    MOCK = "mock", "Mock"
    CASH = "cash", "Cash"
    CARD = "card", "Card"
    ONLINE_GATEWAY = "online_gateway", "Online Gateway"


class PaymentTransactionType(models.TextChoices):
    """Payment transaction type choices."""

    INITIATED = "initiated", "Initiated"
    PAID = "paid", "Paid"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"
    REFUNDED = "refunded", "Refunded"
