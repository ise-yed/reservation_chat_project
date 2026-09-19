from rest_framework import serializers

from apps.chat.enums import MessageType
from apps.chat.models import Conversation, Message
from apps.users.api.v1.serializers.users import UserReadSerializer


class MessageReadSerializer(serializers.ModelSerializer):
    """Serializer for reading messages. Masks deleted message content."""
    sender_id = serializers.UUIDField(source="sender.id", read_only=True)

    class Meta:
        model = Message
        fields = (
            "id",
            "sender_id",
            "type",
            "content",
            "attachment",
            "file_name",
            "file_size",
            "mime_type",
            "is_deleted",
            "deleted_at",
            "created_at",
        )

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if ret.get("is_deleted"):
            ret["content"] = ""
            ret["attachment"] = None
            ret["file_name"] = None
            ret["file_size"] = None
            ret["mime_type"] = None
            ret["type"] = MessageType.TEXT
        return ret


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for sending new messages."""
    class Meta:
        model = Message
        fields = ("type", "content", "attachment")


class ConversationReadSerializer(serializers.ModelSerializer):
    """Serializer for listing conversations in the Inbox."""
    customer = UserReadSerializer(read_only=True)
    provider = UserReadSerializer(read_only=True)
    last_message = MessageReadSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = (
            "id",
            "customer",
            "provider",
            "last_message",
            "patient_last_read_message",
            "doctor_last_read_message",
            "unread_count",
            "created_at",
            "updated_at",
        )

    def get_unread_count(self, obj):
        request = self.context.get("request")
        if not request or not request.user:
            return 0

        user = request.user
        if user == obj.customer:
            last_read = obj.patient_last_read_message
        elif user == obj.provider:
            last_read = obj.doctor_last_read_message
        else:
            return 0

        # محاسبه تعداد پیام‌های خوانده‌نشده
        qs = Message.objects.filter(conversation=obj, is_deleted=False)
        if last_read:
            qs = qs.filter(created_at__gt=last_read.created_at)

        return qs.count()


class ReadPointerUpdateSerializer(serializers.Serializer):
    """Serializer for updating the user's read pointer."""
    last_read_message_id = serializers.UUIDField()
