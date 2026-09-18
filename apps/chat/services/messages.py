from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.chat.enums import MessageType
from apps.chat.models import Message
from apps.chat.services.permissions import can_send_message


@transaction.atomic
def send_message(*, conversation, sender, msg_type=MessageType.TEXT, content="", attachment=None) -> Message:
    if not can_send_message(conversation=conversation, user=sender):
        raise PermissionDenied("You do not have permission to send messages in this conversation at this time.")

    content = content.strip() if content else ""
    
    if msg_type == MessageType.TEXT:
        if not content:
            raise ValidationError({"content": ["Text content is required for text messages."]})
        if attachment:
            raise ValidationError({"attachment": ["Text messages cannot have attachments."]})
            
    elif msg_type in [MessageType.IMAGE, MessageType.DOCUMENT]:
        if not attachment:
            raise ValidationError({"attachment": [f"Attachment is required for {msg_type} messages."]})
        
        # تشخیص فرمت ساده برای MVP (نسخه پیشرفته در فاز ۱۰)
        content_type = getattr(attachment, "content_type", "") or ""
        if msg_type == MessageType.IMAGE and not content_type.startswith("image/"):
            raise ValidationError({"attachment": ["File must be an image type (e.g., image/jpeg, image/png)."]})
        if msg_type == MessageType.DOCUMENT and content_type.startswith("image/"):
            raise ValidationError({"attachment": ["Images should be sent as IMAGE type, not DOCUMENT."]})
            
    message = Message.objects.create(
        conversation=conversation,
        sender=sender,
        type=msg_type,
        content=content,
        attachment=attachment,
    )

    if attachment:
        message.file_name = attachment.name
        message.file_size = attachment.size
        message.mime_type = getattr(attachment, "content_type", "") or "application/octet-stream"
        message.save(update_fields=["file_name", "file_size", "mime_type"])

    conversation.last_message = message
    conversation.save(update_fields=["last_message", "updated_at"])

    return message


@transaction.atomic
def delete_message(*, message, actor) -> Message:
    if actor != message.conversation.provider:
        raise PermissionDenied("Only the doctor is allowed to delete messages.")

    if message.is_deleted:
        return message

    message.is_deleted = True
    message.deleted_at = timezone.now()
    message.deleted_by = actor
    message.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])

    return message


@transaction.atomic
def update_read_pointer(*, conversation, user, last_read_message) -> None:
    if last_read_message.conversation_id != conversation.id:
        raise ValidationError("Message does not belong to this conversation.")

    if user == conversation.customer:
        if not conversation.patient_last_read_message or conversation.patient_last_read_message.created_at < last_read_message.created_at:
            conversation.patient_last_read_message = last_read_message
            conversation.save(update_fields=["patient_last_read_message", "updated_at"])
            
    elif user == conversation.provider:
        if not conversation.doctor_last_read_message or conversation.doctor_last_read_message.created_at < last_read_message.created_at:
            conversation.doctor_last_read_message = last_read_message
            conversation.save(update_fields=["doctor_last_read_message", "updated_at"])