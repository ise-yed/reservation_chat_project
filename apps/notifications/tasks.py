from celery import shared_task
from django.core.exceptions import ValidationError

from apps.notifications.channels import EmailChannel
from apps.notifications.channels.push import PushChannel
from apps.notifications.enums import (
    NotificationChannel,
    NotificationDeliveryStatus,
)
from apps.notifications.models import NotificationDelivery
from apps.notifications.services import (
    mark_delivery_as_failed,
    mark_delivery_as_sent,
)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_delivery_task(self, delivery_id: str) -> None:
    """
    Send a notification delivery through its configured channel.

    The task will retry up to 3 times with 60 second delays between retries.
    Only after all retries are exhausted, the delivery is marked as FAILED.
    """
    try:
        delivery = NotificationDelivery.objects.get(id=delivery_id)
    except (NotificationDelivery.DoesNotExist, ValidationError, ValueError):
        return

    if delivery.status != NotificationDeliveryStatus.PENDING:
        return

    try:
        if delivery.channel == NotificationChannel.EMAIL:
            EmailChannel().send(
                recipient=delivery.recipient,
                subject=delivery.subject,
                body=delivery.body,
            )
        elif delivery.channel == NotificationChannel.PUSH:
            PushChannel().send(
                recipient=delivery.recipient,
                subject=delivery.subject,
                body=delivery.body,
                data=delivery.data
            )
        else:
            mark_delivery_as_failed(
                delivery=delivery,
                error_message=f"Unsupported notification channel: {delivery.channel}",
            )
            return

    except Exception as exc:
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            mark_delivery_as_failed(delivery=delivery, error_message=str(exc))
            return

    mark_delivery_as_sent(delivery=delivery)
