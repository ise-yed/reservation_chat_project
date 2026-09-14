import pytest
from django.utils import timezone

from apps.notifications.enums import (
    NotificationChannel,
    NotificationDeliveryStatus,
    NotificationType,
)
from apps.notifications.models import Notification, NotificationDelivery
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestNotificationModel:
    """Tests for Notification model."""

    def test_create_notification_success(self):
        """Test creating a notification successfully."""
        user = UserFactory()
        notification = Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Password Changed",
            message="Your password has been changed successfully.",
        )

        assert notification.id is not None
        assert notification.user == user
        assert notification.type == NotificationType.PASSWORD_CHANGED
        assert notification.title == "Password Changed"
        assert notification.is_read is False
        assert notification.read_at is None

    def test_notification_str_method(self):
        """Test notification string representation."""
        user = UserFactory(email="test@example.com")
        notification = Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Test Title",
            message="Test Message",
        )

        assert str(notification) == f"{user} - Test Title"

    def test_notification_default_values(self):
        """Test notification default field values."""
        user = UserFactory()
        notification = Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Title",
            message="Message",
        )

        assert notification.is_read is False
        assert notification.read_at is None
        assert notification.data == {}
        assert notification.related_object_type == ""
        assert notification.related_object_id is None

    def test_notification_with_related_object(self):
        """Test notification with related object fields."""
        user = UserFactory()
        notification = Notification.objects.create(
            user=user,
            type=NotificationType.APPOINTMENT_CREATED,
            title="Appointment Created",
            message="Your appointment has been created.",
            related_object_type="appointment",
            related_object_id=123,
        )

        assert notification.related_object_type == "appointment"
        assert notification.related_object_id == 123

    def test_notification_ordering(self):
        """Test notifications are ordered by created_at descending."""
        user = UserFactory()
        notif1 = Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="First",
            message="First message",
        )
        notif2 = Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Second",
            message="Second message",
        )

        notifications = Notification.objects.filter(user=user)
        assert notifications[0] == notif2  # Most recent first
        assert notifications[1] == notif1

    def test_notification_mark_as_read(self):
        """Test marking notification as read."""
        user = UserFactory()
        notification = Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Title",
            message="Message",
        )

        assert notification.is_read is False
        assert notification.read_at is None

        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()

        notification.refresh_from_db()
        assert notification.is_read is True
        assert notification.read_at is not None


class TestNotificationDeliveryModel:
    """Tests for NotificationDelivery model."""

    def test_create_delivery_success(self):
        """Test creating a delivery log successfully."""
        user = UserFactory()
        delivery = NotificationDelivery.objects.create(
            user=user,
            channel=NotificationChannel.EMAIL,
            type=NotificationType.PASSWORD_CHANGED,
            recipient=user.email,
            subject="Test Subject",
            body="Test Body",
        )

        assert delivery.id is not None
        assert delivery.user == user
        assert delivery.channel == NotificationChannel.EMAIL
        assert delivery.status == NotificationDeliveryStatus.PENDING
        assert delivery.sent_at is None

    def test_delivery_str_method(self):
        """Test delivery string representation."""
        user = UserFactory(email="test@example.com")
        delivery = NotificationDelivery.objects.create(
            user=user,
            channel=NotificationChannel.EMAIL,
            type=NotificationType.PASSWORD_CHANGED,
            recipient=user.email,
        )

        assert str(delivery) == f"{delivery.channel} - {delivery.recipient} - {delivery.status}"

    def test_delivery_with_notification_relation(self):
        """Test delivery linked to a notification."""
        user = UserFactory()
        notification = Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Title",
            message="Message",
        )
        delivery = NotificationDelivery.objects.create(
            notification=notification,
            user=user,
            channel=NotificationChannel.EMAIL,
            type=NotificationType.PASSWORD_CHANGED,
            recipient=user.email,
        )

        assert delivery.notification == notification
        assert delivery in notification.deliveries.all()

    def test_delivery_status_transitions(self):
        """Test delivery status changes."""
        user = UserFactory()
        delivery = NotificationDelivery.objects.create(
            user=user,
            channel=NotificationChannel.EMAIL,
            type=NotificationType.PASSWORD_CHANGED,
            recipient=user.email,
        )

        assert delivery.status == NotificationDeliveryStatus.PENDING

        delivery.status = NotificationDeliveryStatus.SENT
        delivery.sent_at = timezone.now()
        delivery.save()

        delivery.refresh_from_db()
        assert delivery.status == NotificationDeliveryStatus.SENT
        assert delivery.sent_at is not None

    def test_delivery_error_message(self):
        """Test delivery error message storage."""
        user = UserFactory()
        delivery = NotificationDelivery.objects.create(
            user=user,
            channel=NotificationChannel.EMAIL,
            type=NotificationType.PASSWORD_CHANGED,
            recipient=user.email,
            status=NotificationDeliveryStatus.FAILED,
            error_message="SMTP connection failed",
        )

        assert delivery.status == NotificationDeliveryStatus.FAILED
        assert delivery.error_message == "SMTP connection failed"

    def test_delivery_on_delete_set_null(self):
        """Test delivery.user becomes null when user is deleted."""
        user = UserFactory()
        delivery = NotificationDelivery.objects.create(
            user=user,
            channel=NotificationChannel.EMAIL,
            type=NotificationType.PASSWORD_CHANGED,
            recipient=user.email,
        )

        user.delete()
        delivery.refresh_from_db()
        assert delivery.user is None
