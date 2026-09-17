from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.db import models

from apps.chat.enums import MessageType
from apps.common.models import BaseModel


def message_attachment_upload_to(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"chat/messages/{instance.conversation_id}/{uuid4().hex}{extension}"


class Message(BaseModel):
    conversation = models.ForeignKey(
        "chat.Conversation", 
        on_delete=models.CASCADE, 
        related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="sent_messages"
    )
    type = models.CharField(
        max_length=10, 
        choices=MessageType.choices, 
        default=MessageType.TEXT
    )
    content = models.TextField(blank=True)
    
    attachment = models.FileField(upload_to=message_attachment_upload_to, blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveBigIntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=150, blank=True)
    
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="+"
    )

    class Meta:
        db_table = "chat_messages"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
        ]

    def __str__(self):
        return f"{self.sender_id}: {self.content[:30]}"