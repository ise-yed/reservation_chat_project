import pytest
from django.utils import timezone

from apps.chat.api.v1.serializers.chat import MessageReadSerializer
from apps.chat.enums import MessageType
from apps.chat.tests.factories import MessageFactory

pytestmark = pytest.mark.django_db


class TestMessageSerializers:
    def test_normal_message_serialization(self):
        msg = MessageFactory(
            content="Sensitive Medical Data",
            type=MessageType.TEXT,
            is_deleted=False
        )
        serializer = MessageReadSerializer(msg)
        data = serializer.data

        assert data["content"] == "Sensitive Medical Data"
        assert data["is_deleted"] is False

    def test_tombstone_masking_for_deleted_message(self):
        msg = MessageFactory(
            content="Sensitive Medical Data",
            type=MessageType.DOCUMENT,
            file_name="blood_test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            is_deleted=True,
            deleted_at=timezone.now()
        )
        serializer = MessageReadSerializer(msg)
        data = serializer.data

        # دیتای اصلی باید کاملاً سانسور شود
        assert data["is_deleted"] is True
        assert data["content"] == ""
        assert data["attachment"] is None
        assert data["file_name"] is None
        assert data["file_size"] is None
        assert data["mime_type"] is None
        # برای جلوگیری از کرش فلاتر در رندر فایل حذف شده، نوع باید متن باشد
        assert data["type"] == MessageType.TEXT
