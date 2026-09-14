from django.db import transaction
from django.utils import timezone

from apps.notifications.enums import (
    NotificationChannel,
    NotificationDeliveryStatus,
)
from apps.notifications.models import Notification, NotificationDelivery


@transaction.atomic
def create_notification(
    *,
    user,
    notification_type,
    title,
    message,
    related_object_type="",
    related_object_id=None,
    data=None,
):
    """Create an in-app notification for a user."""
    return Notification.objects.create(
        user=user,
        type=notification_type,
        title=title,
        message=message,
        related_object_type=related_object_type,
        related_object_id=related_object_id,
        data=data or {},
    )


@transaction.atomic
def create_email_delivery(
    *,
    recipient,
    notification_type,
    user=None,
    notification=None,
    subject="",
    body="",
    data=None,
):
    """Create an email delivery log entry."""
    return NotificationDelivery.objects.create(
        notification=notification,
        user=user,
        channel=NotificationChannel.EMAIL,
        type=notification_type,
        recipient=recipient,
        subject=subject,
        body=body,
        status=NotificationDeliveryStatus.PENDING,
        data=data or {},
    )


@transaction.atomic
def mark_notification_as_read(*, notification: Notification) -> Notification:
    """Mark a single notification as read."""
    if notification.is_read:
        return notification

    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save(update_fields=["is_read", "read_at"])

    return notification


@transaction.atomic
def mark_notification_as_unread(*, notification: Notification) -> Notification:
    """Mark a single notification as unread."""
    if not notification.is_read:
        return notification

    notification.is_read = False
    notification.read_at = None
    notification.save(update_fields=["is_read", "read_at"])

    return notification


@transaction.atomic
def mark_all_notifications_as_read(*, user) -> int:
    """Mark all unread notifications of a user as read."""
    updated_count = Notification.objects.filter(
        user=user,
        is_read=False,
    ).update(
        is_read=True,
        read_at=timezone.now(),
    )
    return updated_count


@transaction.atomic
def mark_delivery_as_sent(*, delivery: NotificationDelivery) -> NotificationDelivery:
    """Mark a delivery log entry as sent."""
    delivery.status = NotificationDeliveryStatus.SENT
    delivery.sent_at = timezone.now()
    delivery.error_message = ""
    delivery.save(update_fields=["status", "sent_at", "error_message", "updated_at"])

    return delivery


@transaction.atomic
def mark_delivery_as_failed(
    *,
    delivery: NotificationDelivery,
    error_message: str,
) -> NotificationDelivery:
    """Mark a delivery log entry as failed."""
    delivery.status = NotificationDeliveryStatus.FAILED
    delivery.error_message = error_message
    delivery.save(update_fields=["status", "error_message", "updated_at"])

    return delivery


def enqueue_notification_delivery(*, delivery: NotificationDelivery) -> None:
    """Queue a notification delivery for async sending."""
    from apps.notifications.tasks import send_notification_delivery_task

    transaction.on_commit(lambda: send_notification_delivery_task.delay(str(delivery.id)))


@transaction.atomic
def send_email_notification(
    *,
    recipient,
    notification_type,
    user=None,
    notification=None,
    subject="",
    body="",
    data=None,
) -> NotificationDelivery:
    """Create and queue an email notification delivery."""
    delivery = create_email_delivery(
        recipient=recipient,
        notification_type=notification_type,
        user=user,
        notification=notification,
        subject=subject,
        body=body,
        data=data,
    )
    enqueue_notification_delivery(delivery=delivery)

    return delivery
