import pytest
from django.core.exceptions import ObjectDoesNotExist

from apps.notifications.enums import NotificationType
from apps.notifications.models import Notification
from apps.notifications.selectors import (
    get_unread_user_notifications,
    get_user_notification_by_id,
    get_user_notifications,
)
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestGetUserNotifications:
    """Tests for get_user_notifications selector."""

    def test_get_user_notifications_returns_all(self):
        """Test getting all notifications for a user."""
        user1 = UserFactory()
        user2 = UserFactory()

        Notification.objects.create(
            user=user1,
            type=NotificationType.PASSWORD_CHANGED,
            title="Title 1",
            message="Message 1",
        )
        Notification.objects.create(
            user=user1,
            type=NotificationType.PASSWORD_CHANGED,
            title="Title 2",
            message="Message 2",
        )
        Notification.objects.create(
            user=user2,
            type=NotificationType.PASSWORD_CHANGED,
            title="Title 3",
            message="Message 3",
        )

        result = get_user_notifications(user=user1)

        assert result.count() == 2
        assert all(n.user == user1 for n in result)

    def test_get_user_notifications_ordered_by_created_at_desc(self):
        """Test notifications are ordered by created_at descending."""
        user = UserFactory()

        notif1 = Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="First",
            message="First",
        )
        notif2 = Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Second",
            message="Second",
        )

        result = get_user_notifications(user=user)

        assert result[0] == notif2
        assert result[1] == notif1

    def test_get_user_notifications_empty(self):
        """Test getting notifications for user with none."""
        user = UserFactory()

        result = get_user_notifications(user=user)

        assert result.count() == 0


class TestGetUnreadUserNotifications:
    """Tests for get_unread_user_notifications selector."""

    def test_get_unread_notifications_only(self):
        """Test getting only unread notifications."""
        user = UserFactory()

        Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Unread 1",
            message="Message",
            is_read=False,
        )
        Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Unread 2",
            message="Message",
            is_read=False,
        )
        Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Read",
            message="Message",
            is_read=True,
        )

        result = get_unread_user_notifications(user=user)

        assert result.count() == 2
        assert all(n.is_read is False for n in result)

    def test_get_unread_notifications_ordered(self):
        """Test unread notifications are ordered by created_at descending."""
        user = UserFactory()

        notif1 = Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="First",
            message="First",
            is_read=False,
        )
        notif2 = Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Second",
            message="Second",
            is_read=False,
        )

        result = get_unread_user_notifications(user=user)

        assert result[0] == notif2
        assert result[1] == notif1


class TestGetUserNotificationById:
    """Tests for get_user_notification_by_id selector."""

    def test_get_notification_by_id_success(self):
        """Test getting notification by ID for correct user."""
        user = UserFactory()
        notification = Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Title",
            message="Message",
        )

        result = get_user_notification_by_id(user=user, notification_id=notification.id)

        assert result == notification

    def test_get_notification_by_id_wrong_user(self):
        """Test getting notification by ID for wrong user raises error."""
        user1 = UserFactory()
        user2 = UserFactory()
        notification = Notification.objects.create(
            user=user1,
            type=NotificationType.PASSWORD_CHANGED,
            title="Title",
            message="Message",
        )

        with pytest.raises(ObjectDoesNotExist):
            get_user_notification_by_id(user=user2, notification_id=notification.id)

    def test_get_notification_by_id_not_found(self):
        """Test getting non-existent notification."""
        user = UserFactory()

        with pytest.raises(ObjectDoesNotExist):
            get_user_notification_by_id(user=user, notification_id=99999)
