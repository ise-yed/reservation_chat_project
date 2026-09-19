from django.db import models


class PaymentMethod(models.TextChoices):
    ONLINE = "online", "Online"
    IN_PERSON = "in_person", "In person (at the clinic)"


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"
    REFUNDED = "refunded", "Refunded"
