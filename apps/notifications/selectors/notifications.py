import uuid

from django.db.models import QuerySet

from apps.notifications.models import Notification


def get_user_notifications(*, user) -> QuerySet[Notification]:
    """Return all notifications for a user."""
    return Notification.objects.filter(user=user).order_by("-created_at")


def get_unread_user_notifications(*, user) -> QuerySet[Notification]:
    """Return unread notifications for a user."""
    return Notification.objects.filter(user=user, is_read=False).order_by("-created_at")


def get_user_notification_by_id(*, user, notification_id: int) -> Notification:
    """Return a single notification belonging to a user."""
    if isinstance(notification_id, uuid.UUID):
        notification_id = str(notification_id)
    return Notification.objects.get(user=user, id=notification_id)
