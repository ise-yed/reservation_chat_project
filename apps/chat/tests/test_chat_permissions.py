from datetime import timedelta

import pytest
from django.utils import timezone

from apps.appointments.enums import AppointmentStatus
from apps.appointments.tests.factories import AppointmentFactory
from apps.chat.services.permissions import can_send_message
from apps.chat.tests.factories import ConversationFactory
from apps.offerings.enums import VisitMode
from apps.providers.tests.factories import ProviderProfileFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def chat_setup():
    """Setup base entities for permission matrix testing."""
    conversation = ConversationFactory()
    provider_profile = ProviderProfileFactory(user=conversation.provider)

    return {
        "conversation": conversation,
        "customer": conversation.customer,
        "provider": conversation.provider,
        "provider_profile": provider_profile,
        "stranger": UserFactory(),
    }


class TestChatPermissionMatrix:
    """
    Test matrix exactly as defined in V4 Document Phase 7:
    | Actor    | Condition         | Result |
    """

    @pytest.mark.parametrize("time_offset, expected", [
        (-1, False),  # بیمار | قبل از شروع | ممنوع
        (0, True),    # بیمار | دقیقاً start_at | مجاز
        (15, True),   # بیمار | داخل بازه | مجاز
        (30, False),  # بیمار | دقیقاً end_at | ممنوع
        (45, False),  # بیمار | بعد از پایان | ممنوع
    ])
    def test_patient_time_boundaries(self, chat_setup, time_offset, expected):
        setup = chat_setup
        now = timezone.now()

        # حرکت دادن زمان نوبت به جای متوقف کردن زمان پایتون (ضدگلوله برای دیتابیس)
        start_at = now - timedelta(minutes=time_offset)
        end_at = start_at + timedelta(minutes=30)

        AppointmentFactory(
            customer=setup["customer"],
            provider=setup["provider_profile"],
            visit_mode=VisitMode.ONLINE_CHAT,
            status=AppointmentStatus.CONFIRMED,
            start_at=start_at,
            end_at=end_at,
            blocked_start_at=start_at,
            blocked_end_at=end_at,
        )

        result = can_send_message(conversation=setup["conversation"], user=setup["customer"])
        assert result is expected

    @pytest.mark.parametrize("status, expected", [
        (AppointmentStatus.PENDING, False),               # بیمار | Pending | ممنوع
        (AppointmentStatus.COMPLETED, False),             # بیمار | Completed | ممنوع
        (AppointmentStatus.CANCELLED_BY_CUSTOMER, False), # بیمار | Cancelled | ممنوع
        (AppointmentStatus.CONFIRMED, True),              # بیمار | Confirmed | مجاز (به شرط زمان)
    ])
    def test_patient_appointment_statuses(self, chat_setup, status, expected):
        setup = chat_setup
        now = timezone.now()

        # تنظیم نوبت طوری که ۵ دقیقه از شروع آن گذشته باشد (در حالت فعال)
        start_at = now - timedelta(minutes=5)
        end_at = start_at + timedelta(minutes=30)

        AppointmentFactory(
            customer=setup["customer"],
            provider=setup["provider_profile"],
            visit_mode=VisitMode.ONLINE_CHAT,
            status=status,
            start_at=start_at,
            end_at=end_at,
            blocked_start_at=start_at,
            blocked_end_at=end_at,
        )

        result = can_send_message(conversation=setup["conversation"], user=setup["customer"])
        assert result is expected

    def test_patient_in_person_appointment(self, chat_setup):
        """بیمار | نوبت حضوری | ممنوع"""
        setup = chat_setup
        now = timezone.now()

        start_at = now - timedelta(minutes=5)
        end_at = start_at + timedelta(minutes=30)

        AppointmentFactory(
            customer=setup["customer"],
            provider=setup["provider_profile"],
            visit_mode=VisitMode.IN_PERSON,
            status=AppointmentStatus.CONFIRMED,
            start_at=start_at,
            end_at=end_at,
            blocked_start_at=start_at,
            blocked_end_at=end_at,
        )

        result = can_send_message(conversation=setup["conversation"], user=setup["customer"])
        assert result is False

    def test_doctor_can_send_anytime(self, chat_setup):
        """پزشک | هر زمان | مجاز"""
        setup = chat_setup

        result = can_send_message(conversation=setup["conversation"], user=setup["provider"])
        assert result is True

    def test_third_party_is_forbidden(self, chat_setup):
        """شخص ثالث | هر زمان | ممنوع"""
        setup = chat_setup

        result = can_send_message(conversation=setup["conversation"], user=setup["stranger"])
        assert result is False
