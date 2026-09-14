from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.notifications.enums import (
    NotificationChannel,
    NotificationDeliveryStatus,
    NotificationType,
)
from apps.notifications.models import Notification, NotificationDelivery
from apps.notifications.services import (
    create_email_delivery,
    create_notification,
    mark_all_notifications_as_read,
    mark_delivery_as_failed,
    mark_delivery_as_sent,
    mark_notification_as_read,
    mark_notification_as_unread,
    send_email_notification,
)
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestCreateNotification:
    """Tests for create_notification service."""

    def test_create_notification_minimal(self):
        """Test creating notification with minimal fields."""
        user = UserFactory()

        notification = create_notification(
            user=user,
            notification_type=NotificationType.PASSWORD_CHANGED,
            title="Password Changed",
            message="Your password has been changed.",
        )

        assert notification.id is not None
        assert notification.user == user
        assert notification.type == NotificationType.PASSWORD_CHANGED
        assert notification.title == "Password Changed"
        assert notification.message == "Your password has been changed."
        assert notification.data == {}

    def test_create_notification_with_related_object(self):
        """Test creating notification with related object."""
        user = UserFactory()

        notification = create_notification(
            user=user,
            notification_type=NotificationType.APPOINTMENT_CREATED,
            title="Appointment Created",
            message="New appointment scheduled",
            related_object_type="appointment",
            related_object_id=456,
            data={"appointment_id": 456},
        )

        assert notification.related_object_type == "appointment"
        assert notification.related_object_id == 456
        assert notification.data == {"appointment_id": 456}


class TestCreateEmailDelivery:
    """Tests for create_email_delivery service."""

    def test_create_email_delivery_success(self):
        """Test creating email delivery log."""
        user = UserFactory()

        delivery = create_email_delivery(
            recipient=user.email,
            notification_type=NotificationType.PASSWORD_CHANGED,
            user=user,
            subject="Test Subject",
            body="Test Body",
        )

        assert delivery.id is not None
        assert delivery.channel == NotificationChannel.EMAIL
        assert delivery.recipient == user.email
        assert delivery.type == NotificationType.PASSWORD_CHANGED
        assert delivery.status == NotificationDeliveryStatus.PENDING

    def test_create_email_delivery_without_user(self):
        """Test creating email delivery without user."""
        delivery = create_email_delivery(
            recipient="anonymous@example.com",
            notification_type=NotificationType.PASSWORD_RESET_REQUESTED,
            subject="Reset Password",
            body="Click link to reset",
        )

        assert delivery.user is None
        assert delivery.recipient == "anonymous@example.com"


class TestMarkNotificationAsRead:
    """Tests for mark_notification_as_read service."""

    def test_mark_unread_as_read(self):
        """Test marking unread notification as read."""
        user = UserFactory()
        notification = Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Title",
            message="Message",
            is_read=False,
        )

        result = mark_notification_as_read(notification=notification)

        assert result.is_read is True
        assert result.read_at is not None

    def test_mark_already_read_notification(self):
        """Test marking already read notification (should do nothing)."""
        user = UserFactory()
        read_at = timezone.now()
        notification = Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Title",
            message="Message",
            is_read=True,
            read_at=read_at,
        )

        result = mark_notification_as_read(notification=notification)

        assert result.is_read is True
        assert result.read_at == read_at  # Unchanged


class TestMarkNotificationAsUnread:
    """Tests for mark_notification_as_unread service."""

    def test_mark_read_as_unread(self):
        """Test marking read notification as unread."""
        user = UserFactory()
        notification = Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Title",
            message="Message",
            is_read=True,
            read_at=timezone.now(),
        )

        result = mark_notification_as_unread(notification=notification)

        assert result.is_read is False
        assert result.read_at is None

    def test_mark_already_unread_notification(self):
        """Test marking already unread notification (should do nothing)."""
        user = UserFactory()
        notification = Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Title",
            message="Message",
            is_read=False,
            read_at=None,
        )

        result = mark_notification_as_unread(notification=notification)

        assert result.is_read is False
        assert result.read_at is None


class TestMarkAllNotificationsAsRead:
    """Tests for mark_all_notifications_as_read service."""

    def test_mark_all_unread_as_read(self):
        """Test marking all unread notifications as read."""
        user = UserFactory()

        # Create multiple unread notifications
        Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Title 1",
            message="Message 1",
            is_read=False,
        )
        Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Title 2",
            message="Message 2",
            is_read=False,
        )

        updated_count = mark_all_notifications_as_read(user=user)

        assert updated_count == 2
        assert Notification.objects.filter(user=user, is_read=False).count() == 0

    def test_mark_all_with_already_read(self):
        """Test marking all when some are already read."""
        user = UserFactory()

        Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Read",
            message="Read message",
            is_read=True,
        )
        Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Unread",
            message="Unread message",
            is_read=False,
        )

        updated_count = mark_all_notifications_as_read(user=user)

        assert updated_count == 1
        assert Notification.objects.filter(user=user, is_read=False).count() == 0


class TestMarkDelivery:
    """Tests for mark_delivery_as_sent and mark_delivery_as_failed."""

    def test_mark_delivery_as_sent(self):
        """Test marking delivery as sent."""
        user = UserFactory()
        delivery = NotificationDelivery.objects.create(
            user=user,
            channel=NotificationChannel.EMAIL,
            type=NotificationType.PASSWORD_CHANGED,
            recipient=user.email,
            status=NotificationDeliveryStatus.PENDING,
        )

        result = mark_delivery_as_sent(delivery=delivery)

        assert result.status == NotificationDeliveryStatus.SENT
        assert result.sent_at is not None
        assert result.error_message == ""

    def test_mark_delivery_as_failed(self):
        """Test marking delivery as failed."""
        user = UserFactory()
        delivery = NotificationDelivery.objects.create(
            user=user,
            channel=NotificationChannel.EMAIL,
            type=NotificationType.PASSWORD_CHANGED,
            recipient=user.email,
            status=NotificationDeliveryStatus.PENDING,
        )

        result = mark_delivery_as_failed(delivery=delivery, error_message="SMTP connection timeout")

        assert result.status == NotificationDeliveryStatus.FAILED
        assert result.error_message == "SMTP connection timeout"


class TestSendEmailNotification:
    """Tests for send_email_notification service."""

    @patch("apps.notifications.services.notifications.enqueue_notification_delivery")
    def test_send_email_notification_creates_delivery(self, mock_enqueue):
        """Test send_email_notification creates delivery record."""
        user = UserFactory()

        delivery = send_email_notification(
            recipient=user.email,
            notification_type=NotificationType.PASSWORD_CHANGED,
            user=user,
            subject="Test",
            body="Test body",
        )

        assert delivery.id is not None
        assert delivery.channel == NotificationChannel.EMAIL
        assert delivery.status == NotificationDeliveryStatus.PENDING
        mock_enqueue.assert_called_once_with(delivery=delivery)

    @patch("apps.notifications.services.notifications.enqueue_notification_delivery")
    def test_send_email_notification_without_user(self, mock_enqueue):
        """Test send_email_notification without user."""
        delivery = send_email_notification(
            recipient="test@example.com",
            notification_type=NotificationType.PASSWORD_RESET_REQUESTED,
            subject="Reset Password",
            body="Click to reset",
        )

        assert delivery.user is None
        assert delivery.recipient == "test@example.com"
        mock_enqueue.assert_called_once_with(delivery=delivery)
