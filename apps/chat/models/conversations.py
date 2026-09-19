from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class Conversation(BaseModel):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="conversations_as_customer",
    )
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="conversations_as_provider",
    )
    last_message = models.ForeignKey(
        "chat.Message",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    patient_last_read_message = models.ForeignKey(
        "chat.Message",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    doctor_last_read_message = models.ForeignKey(
        "chat.Message",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        db_table = "chat_conversations"
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "provider"],
                name="unique_conversation_per_user_pair",
            ),
            models.CheckConstraint(
                condition=~models.Q(customer=models.F("provider")),
                name="conversation_customer_not_provider",
            )
        ]

    def __str__(self):
        return f"Conversation: {self.customer_id} & {self.provider_id}"
