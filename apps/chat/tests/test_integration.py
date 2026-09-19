from datetime import date, time, timedelta
import pytest
from django.utils import timezone
from django.core.exceptions import PermissionDenied

from apps.appointments.enums import AppointmentStatus
from apps.appointments.services.appointment import create_appointment
from apps.appointments.services.chat_lifecycle import complete_appointment_visit
from apps.availability.tests.factories import WorkingHourFactory
from apps.chat.enums import MessageType
from apps.chat.services.messages import send_message
from apps.offerings.enums import VisitMode
from apps.offerings.tests.factories import OfferingFactory
from apps.providers.tests.factories import ProviderProfileFactory
from apps.users.enums import UserRoles
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def make_aware_datetime(target_date, target_time):
    """تبدیل زمان به تایم‌زونِ محلی سیستم (مثلا Asia/Tehran) برای هم‌ترازی با اسلات‌ها"""
    current_timezone = timezone.get_current_timezone()
    return timezone.make_aware(
        timezone.datetime.combine(target_date, target_time),
        current_timezone,
    )


class TestE2EScenariosV4:
    """Integration Tests based on Section 23 of V4 Document."""

    def test_scenario_1_in_person_appointment(self):
        """نوبت حضوری: نباید Conversation بسازد."""
        customer = UserFactory(role=UserRoles.CUSTOMER)
        provider = ProviderProfileFactory()
        offering = OfferingFactory(
            provider=provider, 
            organization=provider.organization, 
            visit_mode=VisitMode.IN_PERSON, 
            duration_minutes=30
        )
        
        target_date = timezone.localdate() + timedelta(days=1)
        
        WorkingHourFactory(
            provider=provider, 
            weekday=target_date.weekday(), 
            start_time=time(9, 0), 
            end_time=time(12, 0)
        )

        start_at = make_aware_datetime(target_date, time(10, 0))

        appointment = create_appointment(
            customer=customer,
            provider_id=provider.id,
            offering_id=offering.id,
            start_at=start_at,
        )

        assert appointment.visit_mode == VisitMode.IN_PERSON
        assert appointment.conversation is None

    def test_scenario_2_first_online_appointment(self):
        """اولین نوبت آنلاین: بررسی کامل مجوزها قبل، در حین و بعد از بازه زمانی."""
        customer = UserFactory(role=UserRoles.CUSTOMER)
        provider_user = UserFactory(role=UserRoles.PROVIDER)
        provider = ProviderProfileFactory(user=provider_user)
        offering = OfferingFactory(
            provider=provider, 
            organization=provider.organization, 
            visit_mode=VisitMode.ONLINE_CHAT, 
            duration_minutes=30, 
            requires_approval=False
        )

        target_date = timezone.localdate() + timedelta(days=1)
        WorkingHourFactory(
            provider=provider, 
            weekday=target_date.weekday(), 
            start_time=time(9, 0), 
            end_time=time(12, 0)
        )

        start_at = make_aware_datetime(target_date, time(10, 0))

        # 1. ساخت نوبت و چت
        appointment = create_appointment(
            customer=customer, provider_id=provider.id, offering_id=offering.id, start_at=start_at
        )
        assert appointment.conversation is not None

        # 2. قبل از شروع: بیمار ممنوع
        with pytest.raises(PermissionDenied):
            send_message(conversation=appointment.conversation, sender=customer, content="Hi")

        # 3. پزشک در هر زمانی مجاز است
        doc_msg = send_message(conversation=appointment.conversation, sender=provider_user, content="Welcome!")
        assert doc_msg.id is not None

        # شبیه‌سازی شروع نوبت (سفر در زمان به لحظه اجرای نوبت)
        now = timezone.now()
        appointment.start_at = now - timedelta(minutes=5)
        appointment.end_at = now + timedelta(minutes=25)
        appointment.save()

        # 4. در حین بازه: بیمار مجاز
        pat_msg = send_message(conversation=appointment.conversation, sender=customer, content="I'm here")
        assert pat_msg.id is not None

        # شبیه‌سازی پایان نوبت (سفر در زمان به پایان نوبت)
        appointment.start_at = now - timedelta(minutes=35)
        appointment.end_at = now - timedelta(minutes=5)
        appointment.save()

        # 5. پایان زمان: بیمار ممنوع
        with pytest.raises(PermissionDenied):
            send_message(conversation=appointment.conversation, sender=customer, content="Wait")

    def test_scenario_3_early_completion(self):
        """پایان زودتر (توسط پزشک): بستن چت به صورت دستی."""
        customer = UserFactory(role=UserRoles.CUSTOMER)
        provider_user = UserFactory(role=UserRoles.PROVIDER)
        provider = ProviderProfileFactory(user=provider_user)
        offering = OfferingFactory(
            provider=provider, 
            organization=provider.organization, 
            visit_mode=VisitMode.ONLINE_CHAT, 
            duration_minutes=30, 
            requires_approval=False
        )

        target_date = timezone.localdate() + timedelta(days=1)
        WorkingHourFactory(
            provider=provider, 
            weekday=target_date.weekday(), 
            start_time=time(9, 0), 
            end_time=time(12, 0)
        )
        start_at = make_aware_datetime(target_date, time(10, 0))

        appointment = create_appointment(
            customer=customer, provider_id=provider.id, offering_id=offering.id, start_at=start_at
        )

        # سفر در زمان: نوبت را به حالت "در حال اجرا" می‌بریم
        now = timezone.now()
        appointment.start_at = now - timedelta(minutes=5)
        appointment.end_at = now + timedelta(minutes=25)
        appointment.save()

        # 1. بیمار در حال پیام دادن است (بدون خطا)
        send_message(conversation=appointment.conversation, sender=customer, content="I have a question.")

        # 2. پزشک دکمه Complete را می‌زند
        complete_appointment_visit(appointment=appointment, actor=provider_user)

        appointment.refresh_from_db()
        assert appointment.status == AppointmentStatus.COMPLETED

        # 3. ارسال بعدی بیمار رد می‌شود
        with pytest.raises(PermissionDenied):
            send_message(conversation=appointment.conversation, sender=customer, content="Hello?")

        # 4. پزشک همچنان می‌تواند پیام پیگیری بفرستد
        follow_up = send_message(conversation=appointment.conversation, sender=provider_user, content="Take this pill.")
        assert follow_up.id is not None