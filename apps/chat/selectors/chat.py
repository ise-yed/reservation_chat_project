from django.core.exceptions import PermissionDenied
from django.db.models import Q
from rest_framework.exceptions import NotFound

from apps.chat.models import Conversation, Message


def get_user_conversations(user, is_active=None):
    """Return conversations for the user. Optionally filter by active status."""
    queryset = Conversation.objects.filter(
        Q(customer=user) | Q(provider__user=user)
    )
    
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
        
    return queryset.select_related("customer", "provider", "provider__user").order_by("-updated_at")


def get_conversation_or_raise(conversation_id, user) -> Conversation:
    """Get conversation and ensure user is a participant. Allows reading closed chats."""
    try:
        conversation = Conversation.objects.select_related(
            "customer", "provider__user"
        ).get(id=conversation_id)
    except Conversation.DoesNotExist:
        raise NotFound("Conversation not found.")

    if conversation.customer != user and conversation.provider.user != user:
        raise PermissionDenied("You do not have permission to view this conversation.")
        
    return conversation


def get_conversation_messages(conversation_id):
    """Return ordered messages for a specific conversation."""
    return Message.objects.filter(
        conversation_id=conversation_id
    ).select_related("sender").order_by("created_at")