from django.utils import timezone

from apps.appointments.enums import AppointmentStatus
from apps.notifications.events import NotificationEvent, publish_notification_event


def _get_user_display_name(user) -> str:
    full_name = getattr(user, "full_name", "")
    if full_name:
        return full_name

    if hasattr(user, "get_full_name"):
        full_name = user.get_full_name()
        if full_name:
            return full_name

    return getattr(user, "email", "") or str(user)


def _format_datetime(value) -> str:
    if not value:
        return ""

    local_value = timezone.localtime(value)
    return local_value.strftime("%Y-%m-%d %H:%M")


def _get_unique_participants(appointment):
    participants = []
    seen_ids = set()

    customer = appointment.customer
    if customer and customer.id not in seen_ids:
        participants.append(customer)
        seen_ids.add(customer.id)

    provider_user = appointment.provider.user
    if provider_user and provider_user.id not in seen_ids:
        participants.append(provider_user)
        seen_ids.add(provider_user.id)

    return participants


def _build_appointment_context(*, appointment, extra_context=None) -> dict:
    branch_name = ""
    if appointment.branch_id:
        branch_name = getattr(appointment.branch, "name", "") or ""

    context = {
        "related_object_type": "appointment",
        "related_object_id": str(appointment.id),
        "appointment_id": str(appointment.id),
        "appointment_status": appointment.status,
        "organization_id": str(appointment.organization_id),
        "organization_name": appointment.organization.name,
        "branch_id": str(appointment.branch_id) if appointment.branch_id else "",
        "branch_name": branch_name,
        "customer_id": str(appointment.customer_id),
        "customer_email": appointment.customer.email,
        "customer_display_name": _get_user_display_name(appointment.customer),
        "provider_id": str(appointment.provider_id),
        "provider_user_id": str(appointment.provider.user_id),
        "provider_email": appointment.provider.user.email,
        "provider_display_name": _get_user_display_name(appointment.provider.user),
        "offering_id": str(appointment.offering_id),
        "offering_title": appointment.offering.title,
        "start_at": appointment.start_at.isoformat(),
        "end_at": appointment.end_at.isoformat(),
        "start_at_display": _format_datetime(appointment.start_at),
        "end_at_display": _format_datetime(appointment.end_at),
        "price": str(appointment.price),
    }

    if extra_context:
        context.update(extra_context)

    return context


def _publish_to_participants(*, event_name: str, appointment, context: dict) -> None:
    for recipient in _get_unique_participants(appointment):
        publish_notification_event(
            event_name=event_name,
            recipient=recipient,
            context=context,
            run_after_commit=True,
        )


def publish_appointment_created_notification(*, appointment) -> None:
    context = _build_appointment_context(appointment=appointment)

    _publish_to_participants(
        event_name=NotificationEvent.APPOINTMENT_CREATED,
        appointment=appointment,
        context=context,
    )


def publish_appointment_cancelled_notification(*, appointment) -> None:
    cancelled_by_display_name = ""
    if appointment.cancelled_by_id:
        cancelled_by_display_name = _get_user_display_name(appointment.cancelled_by)

    context = _build_appointment_context(
        appointment=appointment,
        extra_context={
            "cancelled_by_id": str(appointment.cancelled_by_id)
            if appointment.cancelled_by_id
            else "",
            "cancelled_by_display_name": cancelled_by_display_name,
            "cancel_reason": appointment.cancel_reason or "-",
        },
    )

    _publish_to_participants(
        event_name=NotificationEvent.APPOINTMENT_CANCELLED,
        appointment=appointment,
        context=context,
    )


def publish_appointment_status_notification(*, appointment) -> None:
    event_map = {
        AppointmentStatus.CONFIRMED: NotificationEvent.APPOINTMENT_CONFIRMED,
        AppointmentStatus.COMPLETED: NotificationEvent.APPOINTMENT_COMPLETED,
        AppointmentStatus.NO_SHOW: NotificationEvent.APPOINTMENT_NO_SHOW,
    }

    event_name = event_map.get(appointment.status)

    if not event_name:
        return

    context = _build_appointment_context(appointment=appointment)

    _publish_to_participants(
        event_name=event_name,
        appointment=appointment,
        context=context,
    )


def publish_appointment_reminder_notification(*, appointment) -> None:
    context = _build_appointment_context(
        appointment=appointment,
        extra_context={
            "reminder_type": "reminder_24h",
        },
    )

    _publish_to_participants(
        event_name=NotificationEvent.APPOINTMENT_REMINDER,
        appointment=appointment,
        context=context,
    )
