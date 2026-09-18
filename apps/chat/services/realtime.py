from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from apps.chat.api.v1.serializers.chat import MessageReadSerializer


def broadcast_new_message(*, message):
    """Broadcasts a newly created message to the conversation group."""
    channel_layer = get_channel_layer()
    
    # استفاده از سریالایزر اصلی برای اطمینان از یکسانی ساختار داده با REST API
    message_data = MessageReadSerializer(message).data
    
    async_to_sync(channel_layer.group_send)(
        f"conversation_{message.conversation_id}",
        {
            "type": "chat_event",
            "event": "message.new",
            "data": message_data,
        }
    )


def broadcast_message_deleted(*, message):
    """Broadcasts that a message was soft-deleted by the doctor (Tombstone)."""
    channel_layer = get_channel_layer()
    
    message_data = MessageReadSerializer(message).data
    
    async_to_sync(channel_layer.group_send)(
        f"conversation_{message.conversation_id}",
        {
            "type": "chat_event",
            "event": "message.deleted",
            "data": message_data,
        }
    )


def broadcast_read_receipt(*, conversation_id, user_id, last_read_message_id):
    """Broadcasts that a user has updated their read pointer."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"conversation_{conversation_id}",
        {
            "type": "chat_event",
            "event": "message.seen",
            "data": {
                "user_id": str(user_id),
                "last_read_message_id": str(last_read_message_id),
            }
        }
    )