from django.core.exceptions import PermissionDenied
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.chat.enums import MessageType
from apps.chat.models import Conversation, Message


@transaction.atomic
def get_or_create_conversation(*, customer, provider) -> tuple[Conversation, bool]:
    """Get existing active conversation or create a new one for this pair."""
    conversation, created = Conversation.objects.get_or_create(
        customer=customer,
        provider=provider,
        is_active=True,
    )
    return conversation, created


@transaction.atomic
def create_message(*, conversation: Conversation, sender, msg_type=MessageType.TEXT, content="", attachment=None) -> Message:
    """Create a message after validating permissions and content."""
    
    # 1. Close Check: Cannot send messages to closed chats (Ended Visits)
    if not conversation.is_active:
        raise PermissionDenied("This visit has ended and the conversation is closed. You cannot send new messages.")

    # 2. Participant Check
    if sender != conversation.customer and sender != conversation.provider.user:
        raise PermissionDenied("You cannot send messages to this conversation.")

    # 3. Validation
    if msg_type == MessageType.TEXT and not content.strip():
        raise ValidationError({"content": ["Text content cannot be empty."]})
        
    if msg_type in [MessageType.FILE, MessageType.VOICE] and not attachment:
        raise ValidationError({"attachment": ["File attachment is required for this message type."]})

    # 4. Creation
    message = Message.objects.create(
        conversation=conversation,
        sender=sender,
        type=msg_type,
        content=content.strip() if content else "",
        attachment=attachment,
    )

    conversation.save(update_fields=["updated_at"])
    return message


@transaction.atomic
def mark_messages_as_read(*, conversation: Conversation, user):
    """Mark all unread messages sent by the OTHER person as read."""
    conversation.messages.exclude(sender=user).filter(is_read=False).update(is_read=True)


@transaction.atomic
def close_conversation(*, conversation: Conversation, user) -> Conversation:
    """End the visit and close the conversation. ONLY THE DOCTOR can perform this."""
    if user != conversation.provider.user:
        raise PermissionDenied("Access denied. Only the doctor (provider) can close this conversation and end the visit.")
        
    conversation.is_active = False
    conversation.save(update_fields=["is_active", "updated_at"])
    return conversation


@transaction.atomic
def delete_message(*, message: Message, user):
    """Hard delete a specific message. ONLY THE DOCTOR can perform this."""
    if user != message.conversation.provider.user:
        raise PermissionDenied("Access denied. Only the doctor (provider) is allowed to delete messages.")
    
    message.delete()