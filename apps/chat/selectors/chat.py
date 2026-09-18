from django.core.exceptions import PermissionDenied
from django.db.models import Q
from rest_framework.exceptions import NotFound

from apps.chat.models import Conversation, Message


def get_user_conversations(user):
    """
    Get all conversations for the user (Inbox).
    Orders by updated_at descending.
    """
    return Conversation.objects.filter(
        Q(customer=user) | Q(provider=user)
    ).select_related(
        "customer", 
        "provider", 
        "last_message", 
        "last_message__sender"
    ).order_by("-updated_at")


def get_conversation_or_raise(conversation_id, user) -> Conversation:
    """
    Safely fetch a conversation, ensuring the user is a participant.
    """
    try:
        conversation = Conversation.objects.select_related(
            "customer", "provider"
        ).get(id=conversation_id)
    except Conversation.DoesNotExist:
        raise NotFound("Conversation not found.")

    if conversation.customer != user and conversation.provider != user:
        raise PermissionDenied("You are not a participant in this conversation.")
        
    return conversation


def get_conversation_messages(conversation):
    """
    Get message history for a conversation.
    Returns QuerySet ordered by -created_at for Cursor Pagination (V4 spec).
    """
    # از آنجایی که Soft Delete داریم، رکوردها بازگردانده می‌شوند (Tombstone)
    # اما در Serializer متن و فایل پیام‌های حذف‌شده پنهان (Mask) خواهند شد.
    return Message.objects.filter(
        conversation=conversation
    ).select_related(
        "sender"
    ).order_by("-created_at")