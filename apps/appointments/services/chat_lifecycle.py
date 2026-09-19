from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.appointments.enums import AppointmentStatus
from apps.appointments.permissions import can_manage_appointment
from apps.appointments.services import update_appointment_status
from apps.offerings.enums import VisitMode


def get_chat_access_status(*, appointment, user) -> dict:
    """Returns chat access status and reason exactly as defined in V4 spec."""
    now = timezone.now()

    is_customer = user == appointment.customer
    is_provider = user == appointment.provider.user

    if not (is_customer or is_provider):
        return _build_access_response(None, now, "not_participant", False, False)

    if appointment.visit_mode != VisitMode.ONLINE_CHAT:
        return _build_access_response(appointment, now, "not_online", False, False)

    reason = _determine_access_reason(appointment, now)

    can_read = appointment.conversation_id is not None

    if is_provider:
        can_send = can_read
    else:
        can_send = can_read and reason == "active"

    return _build_access_response(appointment, now, reason, can_read, can_send)


def complete_appointment_visit(*, appointment, actor):
    """Manually end an online visit by doctor."""

    # 1. چک امنیتی باید در بالاترین سطح باشد تا نشت اطلاعات رخ ندهد
    if not can_manage_appointment(actor, appointment):
        raise PermissionDenied("You are not allowed to update this appointment status.")

    # 2. Idempotency
    if appointment.status == AppointmentStatus.COMPLETED:
        return appointment

    # 3. ولیدیشن‌های بیزینسی
    if appointment.visit_mode != VisitMode.ONLINE_CHAT:
        raise ValidationError("Only online chat appointments can be manually completed.")

    if appointment.status != AppointmentStatus.CONFIRMED:
        raise ValidationError("Only confirmed appointments can be completed.")

    if timezone.now() < appointment.start_at:
        raise ValidationError("Cannot complete an appointment before its start time.")

    return update_appointment_status(
        appointment=appointment,
        actor=actor,
        status=AppointmentStatus.COMPLETED
    )


def _determine_access_reason(appointment, now):
    if appointment.status == AppointmentStatus.PENDING:
        return "pending"
    if appointment.status in [AppointmentStatus.CANCELLED_BY_CUSTOMER, AppointmentStatus.CANCELLED_BY_PROVIDER]:
        return "cancelled"
    if appointment.status == AppointmentStatus.COMPLETED:
        return "completed"

    if now < appointment.start_at:
        return "not_started"
    if now >= appointment.end_at:
        return "ended"

    return "active"


def _build_access_response(appointment, now, reason, can_read, can_send):
    if reason == "not_participant" or not appointment:
        return {
            "conversation_id": None,
            "can_read": False,
            "can_send": False,
            "reason": reason,
            "server_now": now.isoformat(),
            "starts_at": None,
            "ends_at": None,
        }

    return {
        "conversation_id": str(appointment.conversation_id) if appointment.conversation_id else None,
        "can_read": can_read,
        "can_send": can_send,
        "reason": reason,
        "server_now": now.isoformat(),
        "starts_at": appointment.start_at.isoformat(),
        "ends_at": appointment.end_at.isoformat(),
    }
