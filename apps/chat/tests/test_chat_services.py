from datetime import timedelta
import pytest
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.appointments.enums import AppointmentStatus
from apps.appointments.tests.factories import AppointmentFactory
from apps.chat.enums import MessageType
from apps.chat.services.messages import (
    delete_message,
    send_message,
    update_read_pointer,
)
from apps.chat.tests.factories import ConversationFactory, MessageFactory
from apps.offerings.enums import VisitMode
from apps.providers.tests.factories import ProviderProfileFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def service_setup():
    conversation = ConversationFactory()
    provider_profile = ProviderProfileFactory(user=conversation.provider)
    now = timezone.now()
    start_at = now - timedelta(minutes=15)
    end_at = now + timedelta(minutes=15)

    # ایجاد نوبت برای دادن مجوز ارسال پیام به بیمار
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
        "stranger": UserFactory()
    }


class TestSendMessageService:
    def test_send_text_message_success(self, service_setup):
        setup = service_setup
        msg = send_message(
            conversation=setup["conversation"],
            sender=setup["customer"],
            msg_type=MessageType.TEXT,
            content="Hello!"
        )
        assert msg.content == "Hello!"
        assert msg.type == MessageType.TEXT
        # بررسی آپدیت شدن last_message
        setup["conversation"].refresh_from_db()
        assert setup["conversation"].last_message == msg

    def test_send_file_message_success(self, service_setup):
        setup = service_setup
        dummy_file = SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")
        msg = send_message(
            conversation=setup["conversation"],
            sender=setup["provider"],
            msg_type=MessageType.DOCUMENT,
            attachment=dummy_file
        )
        assert msg.type == MessageType.DOCUMENT
        assert msg.file_name == "test.pdf"

    def test_send_message_permission_denied(self, service_setup):
        # شخص ثالث نمی‌تواند پیام بدهد
        with pytest.raises(PermissionDenied):
            send_message(
                conversation=service_setup["conversation"],
                sender=service_setup["stranger"],
                content="Hi"
            )

    def test_text_message_requires_content(self, service_setup):
        with pytest.raises(ValidationError, match="Text content is required"):
            send_message(
                conversation=service_setup["conversation"],
                sender=service_setup["customer"],
                msg_type=MessageType.TEXT,
                content="   "
            )

    def test_file_message_requires_attachment(self, service_setup):
        with pytest.raises(ValidationError, match="Attachment is required"):
            send_message(
                conversation=service_setup["conversation"],
                sender=service_setup["customer"],
                msg_type=MessageType.IMAGE,
                content="Look at this"
            )


class TestDeleteMessageService:
    def test_delete_by_doctor_success(self, service_setup):
        msg = MessageFactory(conversation=service_setup["conversation"])
        deleted_msg = delete_message(message=msg, actor=service_setup["provider"])
        
        assert deleted_msg.is_deleted is True
        assert deleted_msg.deleted_by == service_setup["provider"]
        assert deleted_msg.deleted_at is not None

    def test_delete_by_patient_fails(self, service_setup):
        msg = MessageFactory(conversation=service_setup["conversation"])
        with pytest.raises(PermissionDenied, match="Only the doctor"):
            delete_message(message=msg, actor=service_setup["customer"])

    def test_delete_is_idempotent(self, service_setup):
        msg = MessageFactory(conversation=service_setup["conversation"], is_deleted=True)
        deleted_msg = delete_message(message=msg, actor=service_setup["provider"])
        assert deleted_msg == msg  # نباید خطایی بدهد و همان پیام را برمی‌گرداند


class TestUpdateReadPointerService:
    def test_update_read_pointer_success(self, service_setup):
        setup = service_setup
        msg = MessageFactory(conversation=setup["conversation"])
        
        update_read_pointer(
            conversation=setup["conversation"], 
            user=setup["customer"], 
            last_read_message=msg
        )
        setup["conversation"].refresh_from_db()
        assert setup["conversation"].patient_last_read_message == msg

    def test_update_read_pointer_wrong_conversation(self, service_setup):
        other_conv = ConversationFactory()
        msg_other = MessageFactory(conversation=other_conv)
        
        with pytest.raises(ValidationError, match="does not belong"):
            update_read_pointer(
                conversation=service_setup["conversation"], 
                user=service_setup["customer"], 
                last_read_message=msg_other
            )