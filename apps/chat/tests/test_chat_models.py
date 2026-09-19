import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.chat.enums import MessageType
from apps.chat.models.messages import message_attachment_upload_to
from apps.chat.tests.factories import ConversationFactory, MessageFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestConversationModel:
    def test_create_conversation_success(self):
        """Test successful creation of a permanent conversation between a patient and a doctor."""
        customer = UserFactory(role="customer")
        provider = UserFactory(role="provider")

        conversation = ConversationFactory(customer=customer, provider=provider)

        assert conversation.customer == customer
        assert conversation.provider == provider
        assert conversation.patient_last_read_message is None
        assert conversation.doctor_last_read_message is None
        assert str(conversation) == f"Conversation: {customer.id} & {provider.id}"

    def test_unique_conversation_per_user_pair(self):
        """Test that a patient and a doctor can only have ONE conversation thread forever."""
        customer = UserFactory(role="customer")
        provider = UserFactory(role="provider")

        # ساخت چت اول با موفقیت انجام می‌شود
        ConversationFactory(customer=customer, provider=provider)

        # تلاش برای ساخت چت دوم برای همان دو نفر باید با خطای دیتابیس مواجه شود
        with pytest.raises(IntegrityError):
            ConversationFactory(customer=customer, provider=provider)


class TestMessageModel:
    def test_create_text_message(self):
        """Test successful creation of a basic text message."""
        conversation = ConversationFactory()
        message = MessageFactory(
            conversation=conversation,
            sender=conversation.customer,
            type=MessageType.TEXT,
            content="Hello Doctor",
        )

        assert message.conversation == conversation
        assert message.sender == conversation.customer
        assert message.type == MessageType.TEXT
        assert message.content == "Hello Doctor"
        assert message.is_deleted is False
        assert str(message.sender_id) in str(message)
        assert "Hello Doctor" in str(message)

    def test_message_soft_delete_tombstone(self):
        """Test that soft deleting a message properly updates tombstone fields."""
        conversation = ConversationFactory()
        message = MessageFactory(conversation=conversation)
        now = timezone.now()

        # شبیه‌سازی عمل Soft Delete (که در آینده توسط لایه سرویس انجام خواهد شد)
        message.is_deleted = True
        message.deleted_at = now
        message.deleted_by = conversation.provider
        message.save()

        message.refresh_from_db()
        assert message.is_deleted is True
        assert message.deleted_at == now
        assert message.deleted_by == conversation.provider

    def test_message_attachment_upload_path(self):
        """Test that the attachment upload path is correctly formatted with conversation ID."""
        message = MessageFactory()

        # یک کلاس فرضی برای شبیه‌سازی نمونه (Instance) هنگام آپلود
        class DummyInstance:
            conversation_id = message.conversation.id

        path = message_attachment_upload_to(DummyInstance(), "test_DOCUMENT.PDF")

        assert path.startswith(f"chat/messages/{message.conversation.id}/")
        assert path.endswith(".pdf")
