import uuid

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.notifications.enums import NotificationType
from apps.notifications.models import Notification
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestNotificationListView:
    """Tests for NotificationListView."""

    def test_list_notifications_success(self):
        """Test listing notifications for authenticated user."""
        user = UserFactory()
        client = APIClient()
        client.force_authenticate(user=user)
        url = reverse("notifications:list")

        Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Title 1",
            message="Message 1",
        )
        Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Title 2",
            message="Message 2",
        )

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_list_notifications_unauthenticated(self):
        """Test listing notifications without authentication."""
        client = APIClient()
        url = reverse("notifications:list")

        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_notifications_pagination(self):
        """Test notification list pagination."""
        user = UserFactory()
        client = APIClient()
        client.force_authenticate(user=user)
        url = reverse("notifications:list")

        for i in range(25):
            Notification.objects.create(
                user=user,
                type=NotificationType.PASSWORD_CHANGED,
                title=f"Title {i}",
                message=f"Message {i}",
            )

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert "count" in response.data
        assert response.data["count"] == 25
        assert len(response.data["results"]) == 20

    def test_list_notifications_only_users_own(self):
        """Test user only sees their own notifications."""
        user1 = UserFactory()
        user2 = UserFactory()
        client = APIClient()
        client.force_authenticate(user=user1)
        url = reverse("notifications:list")

        Notification.objects.create(
            user=user1,
            type=NotificationType.PASSWORD_CHANGED,
            title="User1 Title",
            message="User1 Message",
        )
        Notification.objects.create(
            user=user2,
            type=NotificationType.PASSWORD_CHANGED,
            title="User2 Title",
            message="User2 Message",
        )

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["title"] == "User1 Title"


class TestNotificationDetailView:
    """Tests for NotificationDetailView."""

    def test_get_notification_detail_success(self):
        """Test getting single notification detail."""
        user = UserFactory()
        client = APIClient()
        client.force_authenticate(user=user)

        notification = Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Test Title",
            message="Test Message",
        )
        url = reverse("notifications:detail", kwargs={"pk": notification.id})

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # تبدیل UUID به string برای مقایسه
        assert str(response.data["id"]) == str(notification.id)
        assert response.data["title"] == "Test Title"

    def test_get_notification_detail_not_found(self):
        """Test getting non-existent notification."""
        user = UserFactory()
        client = APIClient()
        client.force_authenticate(user=user)
        fake_uuid = uuid.uuid4()
        url = reverse("notifications:detail", kwargs={"pk": fake_uuid})

        response = client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_notification_detail_wrong_user(self):
        """Test getting notification belonging to another user."""
        user1 = UserFactory()
        user2 = UserFactory()
        client = APIClient()
        client.force_authenticate(user=user2)

        notification = Notification.objects.create(
            user=user1,
            type=NotificationType.PASSWORD_CHANGED,
            title="Test Title",
            message="Test Message",
        )
        url = reverse("notifications:detail", kwargs={"pk": notification.id})

        response = client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_notification_detail_unauthenticated(self):
        """Test getting notification without authentication."""
        user = UserFactory()
        client = APIClient()

        notification = Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Test Title",
            message="Test Message",
        )
        url = reverse("notifications:detail", kwargs={"pk": notification.id})

        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestNotificationMarkAsReadView:
    """Tests for NotificationMarkAsReadView."""

    def test_mark_notification_as_read_success(self):
        """Test marking a notification as read."""
        user = UserFactory()
        client = APIClient()
        client.force_authenticate(user=user)

        notification = Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Test Title",
            message="Test Message",
            is_read=False,
        )
        url = reverse("notifications:mark-read", kwargs={"pk": notification.id})

        response = client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_read"] is True

        notification.refresh_from_db()
        assert notification.is_read is True

    def test_mark_notification_as_read_already_read(self):
        """Test marking already read notification."""
        user = UserFactory()
        client = APIClient()
        client.force_authenticate(user=user)

        notification = Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Test Title",
            message="Test Message",
            is_read=True,
        )
        url = reverse("notifications:mark-read", kwargs={"pk": notification.id})

        response = client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_read"] is True

    def test_mark_notification_as_read_not_found(self):
        """Test marking non-existent notification as read."""
        user = UserFactory()
        client = APIClient()
        client.force_authenticate(user=user)
        fake_uuid = uuid.uuid4()
        url = reverse("notifications:mark-read", kwargs={"pk": fake_uuid})

        response = client.post(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_mark_notification_as_read_wrong_user(self):
        """Test marking notification of another user as read."""
        user1 = UserFactory()
        user2 = UserFactory()
        client = APIClient()
        client.force_authenticate(user=user2)

        notification = Notification.objects.create(
            user=user1,
            type=NotificationType.PASSWORD_CHANGED,
            title="Test Title",
            message="Test Message",
            is_read=False,
        )
        url = reverse("notifications:mark-read", kwargs={"pk": notification.id})

        response = client.post(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_mark_notification_as_read_unauthenticated(self):
        """Test marking notification as read without authentication."""
        user = UserFactory()
        client = APIClient()

        notification = Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Test Title",
            message="Test Message",
        )
        url = reverse("notifications:mark-read", kwargs={"pk": notification.id})

        response = client.post(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestNotificationMarkAllAsReadView:
    """Tests for NotificationMarkAllAsReadView."""

    def test_mark_all_as_read_success(self):
        """Test marking all notifications as read."""
        user = UserFactory()
        client = APIClient()
        client.force_authenticate(user=user)
        url = reverse("notifications:mark-all-read")

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

        response = client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["marked_as_read"] == 2
        assert Notification.objects.filter(user=user, is_read=False).count() == 0

    def test_mark_all_as_read_no_unread(self):
        """Test marking all when no unread notifications."""
        user = UserFactory()
        client = APIClient()
        client.force_authenticate(user=user)
        url = reverse("notifications:mark-all-read")

        response = client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["marked_as_read"] == 0

    def test_mark_all_as_read_unauthenticated(self):
        """Test marking all as read without authentication."""
        client = APIClient()
        url = reverse("notifications:mark-all-read")

        response = client.post(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestNotificationSerializers:
    """Tests for notification serializers."""

    def test_notification_serializer_fields(self):
        """Test notification serializer returns correct fields."""
        user = UserFactory()
        notification = Notification.objects.create(
            user=user,
            type=NotificationType.PASSWORD_CHANGED,
            title="Test Title",
            message="Test Message",
            data={"key": "value"},
        )

        client = APIClient()
        client.force_authenticate(user=user)
        url = reverse("notifications:detail", kwargs={"pk": notification.id})

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        expected_fields = [
            "id",
            "type",
            "title",
            "message",
            "is_read",
            "read_at",
            "related_object_type",
            "related_object_id",
            "data",
            "created_at",
        ]
        for field in expected_fields:
            assert field in response.data



class TestFCMDeviceRegisterView:
    """Tests for FCMDeviceRegisterView."""

    def test_register_device_success(self):
        user = UserFactory()
        client = APIClient()
        client.force_authenticate(user=user)
        url = reverse("notifications:device-register")

        payload = {
            "registration_id": "test_fcm_token_12345",
            "device_type": "android"
        }

        response = client.post(url, data=payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "Device registered"

        from apps.notifications.models import FCMDevice
        assert FCMDevice.objects.filter(user=user, registration_id="test_fcm_token_12345").exists()

    def test_register_device_unauthenticated(self):
        client = APIClient()
        url = reverse("notifications:device-register")

        response = client.post(url, data={"registration_id": "token"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
