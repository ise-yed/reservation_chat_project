from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APIClient

from apps.appointments.enums import AppointmentStatus
from apps.appointments.services.chat_lifecycle import (
    complete_appointment_visit,
    get_chat_access_status,
)
from apps.appointments.tests.factories import AppointmentFactory
from apps.chat.tests.factories import ConversationFactory
from apps.offerings.enums import VisitMode
from apps.providers.tests.factories import ProviderProfileFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def lifecycle_setup():
    conversation = ConversationFactory()
    provider_profile = ProviderProfileFactory(user=conversation.provider)
    now = timezone.now().replace(microsecond=0)

    return {
        "conversation": conversation,
        "customer": conversation.customer,
        "provider": conversation.provider,
        "provider_profile": provider_profile,
        "stranger": UserFactory(),
        "now": now,
        # نوبت پیش‌فرض در وضعیت فعال است (از 15 دقیقه پیش تا 15 دقیقه آینده)
        "start_at": now - timedelta(minutes=15),
        "end_at": now + timedelta(minutes=15),
    }


class TestChatAccessStatusSelector:
    """Test all 8 reasons for get_chat_access_status logic."""

    @pytest.mark.parametrize("scenario, app_status, visit_mode, time_shift, expected_reason", [
        ("active", AppointmentStatus.CONFIRMED, VisitMode.ONLINE_CHAT, 0, "active"),
        ("pending", AppointmentStatus.PENDING, VisitMode.ONLINE_CHAT, 0, "pending"),
        ("completed", AppointmentStatus.COMPLETED, VisitMode.ONLINE_CHAT, 0, "completed"),
        ("cancelled", AppointmentStatus.CANCELLED_BY_CUSTOMER, VisitMode.ONLINE_CHAT, 0, "cancelled"),
        ("ended", AppointmentStatus.CONFIRMED, VisitMode.ONLINE_CHAT, -30, "ended"), # 30 دقیقه به گذشته (تمام شده)
        ("not_started", AppointmentStatus.CONFIRMED, VisitMode.ONLINE_CHAT, 30, "not_started"), # 30 دقیقه به آینده (شروع نشده)
        ("not_online", AppointmentStatus.CONFIRMED, VisitMode.IN_PERSON, 0, "not_online"),
    ])
    def test_access_reasons(self, lifecycle_setup, scenario, app_status, visit_mode, time_shift, expected_reason):
        setup = lifecycle_setup
        start_at = setup["start_at"] + timedelta(minutes=time_shift)
        end_at = setup["end_at"] + timedelta(minutes=time_shift)

        appointment = AppointmentFactory(
            customer=setup["customer"],
            provider=setup["provider_profile"],
            conversation=setup["conversation"] if visit_mode == VisitMode.ONLINE_CHAT else None,
            status=app_status,
            visit_mode=visit_mode,
            start_at=start_at,
            end_at=end_at,
            blocked_start_at=start_at,
            blocked_end_at=end_at,
        )

        response = get_chat_access_status(appointment=appointment, user=setup["customer"])
        assert response["reason"] == expected_reason
        if expected_reason == "active":
            assert response["can_send"] is True

    def test_not_participant_reason_hides_data(self, lifecycle_setup):
        setup = lifecycle_setup
        appointment = AppointmentFactory(
            customer=setup["customer"],
            provider=setup["provider_profile"],
            visit_mode=VisitMode.ONLINE_CHAT,
            start_at=setup["start_at"],
            end_at=setup["end_at"],
            blocked_start_at=setup["start_at"],
            blocked_end_at=setup["end_at"],
        )

        response = get_chat_access_status(appointment=appointment, user=setup["stranger"])
        assert response["reason"] == "not_participant"
        assert response["conversation_id"] is None
        assert response["starts_at"] is None


class TestCompleteAppointmentVisitService:
    def test_success_complete_by_doctor(self, lifecycle_setup):
        setup = lifecycle_setup
        appointment = AppointmentFactory(
            customer=setup["customer"],
            provider=setup["provider_profile"],
            visit_mode=VisitMode.ONLINE_CHAT,
            status=AppointmentStatus.CONFIRMED,
            start_at=setup["start_at"],
            end_at=setup["end_at"],
            blocked_start_at=setup["start_at"],
            blocked_end_at=setup["end_at"],
        )

        completed_app = complete_appointment_visit(appointment=appointment, actor=setup["provider"])
        assert completed_app.status == AppointmentStatus.COMPLETED

    def test_auth_first_prevents_data_leakage(self, lifecycle_setup):
        """Ensure auth is checked before state validation, preventing data leaks."""
        setup = lifecycle_setup
        # ساخت نوبت حضوری که در شرایط عادی خطای VisitMode می‌دهد
        appointment = AppointmentFactory(
            customer=setup["customer"],
            provider=setup["provider_profile"],
            visit_mode=VisitMode.IN_PERSON,
            status=AppointmentStatus.CONFIRMED,
            start_at=setup["start_at"],
            end_at=setup["end_at"],
            blocked_start_at=setup["start_at"],
            blocked_end_at=setup["end_at"],
        )

        # شخص ثالث اگر درخواست دهد، اول باید خطای مجوز بگیرد نه خطای حالت ویزیت
        with pytest.raises(PermissionDenied):
            complete_appointment_visit(appointment=appointment, actor=setup["stranger"])

    def test_idempotent_complete(self, lifecycle_setup):
        setup = lifecycle_setup
        appointment = AppointmentFactory(
            customer=setup["customer"],
            provider=setup["provider_profile"],
            visit_mode=VisitMode.ONLINE_CHAT,
            status=AppointmentStatus.COMPLETED, # نوبت از قبل تکمیل شده
            start_at=setup["start_at"],
            end_at=setup["end_at"],
            blocked_start_at=setup["start_at"],
            blocked_end_at=setup["end_at"],
        )
        # باید بدون هیچ خطای ولیدیشنی نوبت را برگرداند
        result = complete_appointment_visit(appointment=appointment, actor=setup["provider"])
        assert result.status == AppointmentStatus.COMPLETED

    def test_validation_errors(self, lifecycle_setup):
        setup = lifecycle_setup

        # Test Not Online
        app_in_person = AppointmentFactory(
            provider=setup["provider_profile"],
            visit_mode=VisitMode.IN_PERSON,
            start_at=setup["start_at"],
            end_at=setup["end_at"],
            blocked_start_at=setup["start_at"],
            blocked_end_at=setup["end_at"],
        )
        with pytest.raises(ValidationError, match="Only online"):
            complete_appointment_visit(appointment=app_in_person, actor=setup["provider"])

        # Test Not Confirmed
        app_pending = AppointmentFactory(
            provider=setup["provider_profile"],
            visit_mode=VisitMode.ONLINE_CHAT,
            status=AppointmentStatus.PENDING,
            start_at=setup["start_at"],
            end_at=setup["end_at"],
            blocked_start_at=setup["start_at"],
            blocked_end_at=setup["end_at"],
        )
        with pytest.raises(ValidationError, match="Only confirmed"):
            complete_appointment_visit(appointment=app_pending, actor=setup["provider"])


class TestChatActionsAPI:
    def test_chat_access_view_404_for_stranger(self, lifecycle_setup):
        setup = lifecycle_setup
        appointment = AppointmentFactory(
            customer=setup["customer"],
            provider=setup["provider_profile"],
            visit_mode=VisitMode.ONLINE_CHAT,
            start_at=setup["start_at"],
            end_at=setup["end_at"],
            blocked_start_at=setup["start_at"],
            blocked_end_at=setup["end_at"],
        )
        client = APIClient()
        client.force_authenticate(user=setup["stranger"])

        url = reverse("appointments:appointment-chat-access", kwargs={"appointment_id": appointment.id})
        response = client.get(url)

        # غریبه باید خطای 404 بگیرد تا وجود نوبت فاش نشود
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_chat_access_view_200_for_participant(self, lifecycle_setup):
        setup = lifecycle_setup
        appointment = AppointmentFactory(
            customer=setup["customer"],
            provider=setup["provider_profile"],
            visit_mode=VisitMode.ONLINE_CHAT,
            start_at=setup["start_at"],
            end_at=setup["end_at"],
            blocked_start_at=setup["start_at"],
            blocked_end_at=setup["end_at"],
        )
        client = APIClient()
        client.force_authenticate(user=setup["customer"])

        url = reverse("appointments:appointment-chat-access", kwargs={"appointment_id": appointment.id})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "reason" in response.data

    def test_complete_view_forbidden_for_stranger(self, lifecycle_setup):
        setup = lifecycle_setup
        appointment = AppointmentFactory(
            customer=setup["customer"],
            provider=setup["provider_profile"],
            visit_mode=VisitMode.ONLINE_CHAT,
            start_at=setup["start_at"],
            end_at=setup["end_at"],
            blocked_start_at=setup["start_at"],
            blocked_end_at=setup["end_at"],
        )
        client = APIClient()
        client.force_authenticate(user=setup["stranger"])

        url = reverse("appointments:appointment-complete", kwargs={"appointment_id": appointment.id})
        response = client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
