from django.db.models import QuerySet

from apps.payments.models import Payment


def payment_queryset() -> QuerySet[Payment]:
    """Get base payment queryset with related data."""
    return (
        Payment.objects.select_related(
            "appointment",
            "appointment__customer",
            "appointment__provider",
            "appointment__provider__user",
            "appointment__offering",
            "organization",
            "payer",
            "created_by",
        )
        .prefetch_related("transactions")
        .order_by("-created_at")
    )


def get_payment_by_id(*, payment_id) -> Payment:
    """Get a single payment by ID."""
    return payment_queryset().get(id=payment_id)


def get_user_payments(*, user) -> QuerySet[Payment]:
    """Get payments for a specific user."""
    return payment_queryset().filter(payer=user)


def get_organization_payments(*, organization) -> QuerySet[Payment]:
    """Get payments for a specific organization."""
    return payment_queryset().filter(organization=organization)


def get_appointment_payments(*, appointment) -> QuerySet[Payment]:
    """Get payments for a specific appointment."""
    return payment_queryset().filter(appointment=appointment)
