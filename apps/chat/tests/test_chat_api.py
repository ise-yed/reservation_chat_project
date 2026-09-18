from datetime import timedelta
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.appointments.enums import AppointmentStatus
from apps.appointments.tests.factories import AppointmentFactory
from apps.chat.enums import MessageType
from apps.chat.tests.factories import ConversationFactory, MessageFactory
from apps.offerings.enums import VisitMode
from apps.providers.tests.factories import ProviderProfileFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_setup():
    """Setup active conversation environment for API testing."""
    conversation = ConversationFactory()
    provider_profile = ProviderProfileFactory(user=conversation.provider)
    now = timezone.now()
    start_at = now - timedelta(minutes=15)
    end_at = now + timedelta(minutes=15)

    # ایجاد یک نوبت آنلاین تایید شده تا بیمار بتواند در تست‌ها پیام بفرستد
    AppointmentFactory(
        customer=conversation.customer,
        provider=provider_profile,
        visit_mode=VisitMode.ONLINE_CHAT,
        status=AppointmentStatus.CONFIRMED,
        start_at=start_at,
        end_at=end_at,
        blocked_start_at=start_at,
        blocked_end_at=end_at,
    )

    return {
        "conversation": conversation,
        "customer": conversation.customer,
        "provider": conversation.provider,
        "client": APIClient()
    }


class TestChatAPI:
    def test_get_inbox_conversations(self, api_setup):
        """GET /api/v1/chat/conversations/"""
        client = api_setup["client"]
        client.force_authenticate(user=api_setup["customer"])
        
        url = reverse("chat:conversation-list")
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # به دلیل اینکه از Pagination عمومی استفاده کردیم، داده‌ها داخل results هستند
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == str(api_setup["conversation"].id)

    def test_get_message_history_with_cursor(self, api_setup):
        """GET /api/v1/chat/conversations/{id}/messages/"""
        MessageFactory(conversation=api_setup["conversation"], content="Hello Doctor")
        
        client = api_setup["client"]
        client.force_authenticate(user=api_setup["customer"])
        
        url = reverse("chat:message-list-create", kwargs={"conversation_id": api_setup["conversation"].id})
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert "next" in response.data
        assert "previous" in response.data
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["content"] == "Hello Doctor"

    def test_send_message_success_with_active_appointment(self, api_setup):
        """POST /api/v1/chat/conversations/{id}/messages/"""
        client = api_setup["client"]
        client.force_authenticate(user=api_setup["customer"])
        
        url = reverse("chat:message-list-create", kwargs={"conversation_id": api_setup["conversation"].id})
        payload = {"type": MessageType.TEXT, "content": "I have a headache"}
        response = client.post(url, data=payload, format="json")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["content"] == "I have a headache"

    def test_send_message_fails_without_appointment(self):
        """تست امنیت: بیمار بدون نوبت فعال حق ارسال پیام ندارد"""
        # مکالمه‌ای می‌سازیم که هیچ نوبتی به آن متصل نیست
        conv = ConversationFactory()
        client = APIClient()
        client.force_authenticate(user=conv.customer)
        
        url = reverse("chat:message-list-create", kwargs={"conversation_id": conv.id})
        payload = {"type": MessageType.TEXT, "content": "Hello?"}
        response = client.post(url, data=payload, format="json")
        
        # باید خطای 403 (مجوز رد شد) بگیرد
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_message_by_doctor_success(self, api_setup):
        """DELETE /api/v1/chat/messages/{id}/ by doctor"""
        msg = MessageFactory(conversation=api_setup["conversation"])
        client = api_setup["client"]
        client.force_authenticate(user=api_setup["provider"])
        
        url = reverse("chat:message-detail", kwargs={"message_id": msg.id})
        response = client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        msg.refresh_from_db()
        assert msg.is_deleted is True

    def test_delete_message_by_patient_forbidden(self, api_setup):
        """بیمار نباید بتواند پیامی را پاک کند"""
        msg = MessageFactory(conversation=api_setup["conversation"])
        client = api_setup["client"]
        client.force_authenticate(user=api_setup["customer"])
        
        url = reverse("chat:message-detail", kwargs={"message_id": msg.id})
        response = client.delete(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_tombstone_masks_deleted_content(self, api_setup):
        """تست Tombstone: اطمینان از اینکه پیام پاک شده دیتای مخفی را لو نمی‌دهد"""
        MessageFactory(
            conversation=api_setup["conversation"],
            content="SECRET PATIENT DATA",
            is_deleted=True,
            deleted_at=timezone.now()
        )
        
        client = api_setup["client"]
        client.force_authenticate(user=api_setup["customer"])
        url = reverse("chat:message-list-create", kwargs={"conversation_id": api_setup["conversation"].id})
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        msg_data = response.data["results"][0]
        
        assert msg_data["is_deleted"] is True
        assert msg_data["content"] == ""  # متن کاملاً سانسور شده است
        assert "SECRET PATIENT DATA" not in str(response.data)

    def test_update_read_pointer(self, api_setup):
        """POST /api/v1/chat/conversations/{id}/read/"""
        msg = MessageFactory(conversation=api_setup["conversation"])
        client = api_setup["client"]
        client.force_authenticate(user=api_setup["customer"])
        
        url = reverse("chat:update-read-pointer", kwargs={"conversation_id": api_setup["conversation"].id})
        response = client.post(url, data={"last_read_message_id": str(msg.id)}, format="json")
        
        assert response.status_code == status.HTTP_200_OK
        api_setup["conversation"].refresh_from_db()
        assert api_setup["conversation"].patient_last_read_message == msg
        
        
    def test_unread_count_logic(self, api_setup):
        """تست محاسبه دقیق unread_count قبل و بعد از آپدیت Read Pointer"""
        conv = api_setup["conversation"]
        client = api_setup["client"]
        customer = api_setup["customer"]
        provider = api_setup["provider"]

        # ایجاد ۳ پیام متوالی توسط پزشک
        msg1 = MessageFactory(conversation=conv, sender=provider, content="Message 1")
        msg2 = MessageFactory(conversation=conv, sender=provider, content="Message 2")
        msg3 = MessageFactory(conversation=conv, sender=provider, content="Message 3")

        client.force_authenticate(user=customer)
        list_url = reverse("chat:conversation-list")
        read_url = reverse("chat:update-read-pointer", kwargs={"conversation_id": conv.id})

        # ۱. وضعیت اولیه: بیمار هیچ پیامی را نخوانده است (تعداد باید ۳ باشد)
        response = client.get(list_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["unread_count"] == 3

        # ۲. بیمار فقط تا پیام دوم را می‌خواند
        client.post(read_url, data={"last_read_message_id": str(msg2.id)}, format="json")
        
        response = client.get(list_url)
        assert response.data["results"][0]["unread_count"] == 1  # فقط msg3 خوانده نشده است

        # ۳. بیمار آخرین پیام را هم می‌خواند
        client.post(read_url, data={"last_read_message_id": str(msg3.id)}, format="json")
        
        response = client.get(list_url)
        assert response.data["results"][0]["unread_count"] == 0  # همه خوانده شدند