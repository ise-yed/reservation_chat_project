from django.utils import timezone

from apps.appointments.enums import AppointmentStatus
from apps.appointments.models import Appointment
from apps.offerings.enums import VisitMode


def can_send_message(*, conversation, user) -> bool:
    """
    Check if a user is allowed to send a message in the given conversation.
    Implements Phase 7 V4 logic.
    """
    # 1. پزشکِ همان مکالمه همیشه مجاز است
    if user == conversation.provider:
        return True
        
    # 2. شخص ثالث (کسی که نه بیمار است نه پزشک) همیشه ممنوع است
    if user != conversation.customer:
        return False

    # 3. بررسی مجوز بیمار (فقط در بازه نوبت آنلاین تایید شده مجاز است)
    now = timezone.now()
    
    has_active_appointment = Appointment.objects.filter(
        customer=user,
        provider__user=conversation.provider,
        visit_mode=VisitMode.ONLINE_CHAT,
        status=AppointmentStatus.CONFIRMED,
        start_at__lte=now,
        end_at__gt=now,  # انتهای بازه انحصاری است
    ).exists()

    return has_active_appointment