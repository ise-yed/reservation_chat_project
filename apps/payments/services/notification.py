from django.utils import timezone

from apps.notifications.events import NotificationEvent, publish_notification_event


def _get_user_display_name(user) -> str:
    """Get user display name."""
    if hasattr(user, "full_name") and user.full_name:
        return user.full_name

    if hasattr(user, "get_full_name"):
        full_name = user.get_full_name()
        if full_name:
            return full_name

    return getattr(user, "email", "") or str(user)


def _format_datetime(value) -> str:
    """Format datetime for display."""
    if not value:
        return ""

    return timezone.localtime(value).strftime("%Y-%m-%d %H:%M")


def _build_payment_context(*, payment) -> dict:
    """Build context for payment notifications."""
    appointment = payment.appointment

    return {
        "related_object_type": "payment",
        "related_object_id": str(payment.id),
        "payment_id": str(payment.id),
        "payment_status": payment.status,
        "payment_amount": str(payment.amount),
        "payment_currency": payment.currency,
        "payment_method": payment.method,
        "gateway_reference": payment.gateway_reference,
        "appointment_id": str(appointment.id),
        "appointment_status": appointment.status,
        "appointment_start_at_display": _format_datetime(appointment.start_at),
        "appointment_end_at_display": _format_datetime(appointment.end_at),
        "organization_id": str(payment.organization_id),
        "organization_name": payment.organization.name,
        "offering_id": str(appointment.offering_id),
        "offering_title": appointment.offering.title,
        "customer_id": str(appointment.customer_id),
        "customer_display_name": _get_user_display_name(appointment.customer),
        "provider_id": str(appointment.provider_id),
        "provider_display_name": _get_user_display_name(appointment.provider.user),
        "user_display_name": _get_user_display_name(payment.payer),
    }


def publish_payment_success_notification(*, payment) -> None:
    """Publish payment success notification."""
    publish_notification_event(
        event_name=NotificationEvent.PAYMENT_SUCCESS,
        recipient=payment.payer,
        context=_build_payment_context(payment=payment),
        run_after_commit=True,
    )


def publish_payment_failed_notification(*, payment) -> None:
    """Publish payment failed notification."""
    publish_notification_event(
        event_name=NotificationEvent.PAYMENT_FAILED,
        recipient=payment.payer,
        context=_build_payment_context(payment=payment),
        run_after_commit=True,
    )


def publish_refund_success_notification(*, payment) -> None:
    """Publish refund success notification."""
    publish_notification_event(
        event_name=NotificationEvent.REFUND_SUCCESS,
        recipient=payment.payer,
        context=_build_payment_context(payment=payment),
        run_after_commit=True,
    )
