import uuid
from unittest.mock import patch

import pytest
from django.core.exceptions import ImproperlyConfigured

from apps.authentication.services import (
    build_auth_tokens_for_user,
    change_password,
    register_user,
    request_password_reset,
    reset_password,
)
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestRegisterUser:
    """Tests for register_user function."""

    def test_register_user_success(self):
        """Test successful user registration with valid data."""
        user = register_user(
            email="test@example.com",
            password="SecurePass123!",
            first_name="John",
            last_name="Doe",
            phone_number="09123456789",
            role="customer",
        )

        assert user.email == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.phone_number == "09123456789"
        assert user.role == "customer"
        assert user.check_password("SecurePass123!")
        assert user.is_active

    def test_register_user_minimal_data(self):
        """Test user registration with only required fields."""
        user = register_user(email="minimal@example.com", password="SecurePass123!")

        assert user.email == "minimal@example.com"
        assert user.first_name == ""
        assert user.last_name == ""
        assert user.phone_number == ""
        assert user.role == "customer"
        assert user.check_password("SecurePass123!")

    def test_register_user_duplicate_email(self):
        """Test registration fails with duplicate email."""
        from django.db import IntegrityError

        register_user(email="duplicate@example.com", password="Pass123!")

        with pytest.raises(IntegrityError):
            register_user(email="duplicate@example.com", password="Pass456!")


class TestBuildAuthTokensForUser:
    """Tests for build_auth_tokens_for_user function."""

    def test_build_auth_tokens_success(self):
        """Test token generation returns both access and refresh tokens."""
        user = UserFactory()
        tokens = build_auth_tokens_for_user(user)

        assert "access" in tokens
        assert "refresh" in tokens
        assert isinstance(tokens["access"], str)
        assert isinstance(tokens["refresh"], str)
        assert len(tokens["access"]) > 0
        assert len(tokens["refresh"]) > 0

    def test_tokens_are_different_for_different_users(self):
        """Test different users get different tokens."""
        user1 = UserFactory()
        user2 = UserFactory()

        tokens1 = build_auth_tokens_for_user(user1)
        tokens2 = build_auth_tokens_for_user(user2)

        assert tokens1["access"] != tokens2["access"]
        assert tokens1["refresh"] != tokens2["refresh"]


class TestSendPasswordResetEmail:
    """Tests for send_password_reset_email function."""

    @patch("apps.authentication.services.authentication.publish_notification_event")
    def test_send_password_reset_email_success(self, mock_publish, settings):
        """Test successful password reset email sending."""
        settings.FRONTEND_PASSWORD_RESET_URL = "http://localhost:3000/reset-password"
        user = UserFactory(email="reset@example.com")

        request_password_reset(user=user)

        assert mock_publish.called
        call_args = mock_publish.call_args[1]
        assert call_args["event_name"] == "authentication.password_reset_requested"
        assert call_args["recipient"] == user
        assert "reset_link" in call_args["context"]
        assert "uid" in call_args["context"]["reset_link"]
        assert "token" in call_args["context"]["reset_link"]

    @patch("apps.authentication.services.authentication.publish_notification_event")
    def test_send_password_reset_email_missing_url(self, mock_publish, settings):
        """Test error when FRONTEND_PASSWORD_RESET_URL is not configured."""
        # Remove the setting if exists
        if hasattr(settings, "FRONTEND_PASSWORD_RESET_URL"):
            delattr(settings, "FRONTEND_PASSWORD_RESET_URL")

        user = UserFactory()

        with pytest.raises(ImproperlyConfigured) as exc_info:
            request_password_reset(user=user)

        assert "FRONTEND_PASSWORD_RESET_URL must be configured" in str(exc_info.value)
        assert not mock_publish.called


class TestChangePassword:
    """Tests for change_password function."""

    @patch("apps.authentication.services.authentication.publish_notification_event")
    def test_change_password_success(self, mock_publish):
        """Test successful password change."""
        # UserFactory creates user with password "StrongPass123!" already
        user = UserFactory()

        # Verify initial password works
        assert user.check_password("StrongPass123!")

        updated_user = change_password(user=user, new_password="NewStrongPass456!")

        assert updated_user == user
        user.refresh_from_db()
        assert user.check_password("NewStrongPass456!")
        assert not user.check_password("StrongPass123!")
        assert mock_publish.called

    @patch("apps.authentication.services.authentication.publish_notification_event")
    def test_change_password_publishes_event(self, mock_publish):
        """Test that PASSWORD_CHANGED event is published."""
        user = UserFactory()

        change_password(user=user, new_password="NewPass123!")

        mock_publish.assert_called_once_with(
            event_name="authentication.password_changed", recipient=user
        )


class TestResetPassword:
    """Tests for reset_password function."""

    def test_reset_password_success(self):
        """Test successful password reset with valid token."""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        user = UserFactory()
        old_password = "StrongPass123!"
        assert user.check_password(old_password)  # Verify initial password

        # Encode the user's primary key (UUID)
        uid = urlsafe_base64_encode(force_bytes(str(user.pk)))
        token = default_token_generator.make_token(user)

        success = reset_password(uid=uid, token=token, new_password="NewResetPass789!")

        assert success is True
        user.refresh_from_db()
        assert user.check_password("NewResetPass789!")
        assert not user.check_password(old_password)

    def test_reset_password_invalid_uid(self):
        """Test reset fails with invalid uid."""
        user = UserFactory()
        old_password = "StrongPass123!"
        assert user.check_password(old_password)

        success = reset_password(
            uid="invalid-uid!!", token="some-token", new_password="NewPass123!"
        )

        assert success is False
        user.refresh_from_db()
        assert user.check_password(old_password)  # Still old password

    def test_reset_password_invalid_token(self):
        """Test reset fails with invalid token."""
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        user = UserFactory()
        old_password = "StrongPass123!"
        assert user.check_password(old_password)

        uid = urlsafe_base64_encode(force_bytes(str(user.pk)))

        success = reset_password(uid=uid, token="invalid-token", new_password="NewPass123!")

        assert success is False
        user.refresh_from_db()
        assert user.check_password(old_password)  # Still old password

    def test_reset_password_user_not_found(self):
        """Test reset fails when user doesn't exist."""
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        # Use a valid UUID that doesn't exist in database
        fake_uuid = uuid.uuid4()
        uid = urlsafe_base64_encode(force_bytes(str(fake_uuid)))

        success = reset_password(uid=uid, token="some-token", new_password="NewPass123!")

        assert success is False

    def test_reset_password_weak_password(self):
        """Test reset fails with weak password."""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        user = UserFactory()
        old_password = "StrongPass123!"
        assert user.check_password(old_password)

        uid = urlsafe_base64_encode(force_bytes(str(user.pk)))
        token = default_token_generator.make_token(user)

        success = reset_password(
            uid=uid,
            token=token,
            new_password="123",  # Too short/weak
        )

        assert success is False
        user.refresh_from_db()
        assert user.check_password(old_password)  # Still old password

    def test_reset_password_expired_token(self):
        """Test reset fails with expired token."""
        from unittest.mock import patch

        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        user = UserFactory()
        old_password = "StrongPass123!"
        assert user.check_password(old_password)

        uid = urlsafe_base64_encode(force_bytes(str(user.pk)))

        with patch(
            "django.contrib.auth.tokens.default_token_generator.check_token", return_value=False
        ):
            success = reset_password(uid=uid, token="any-token", new_password="NewPass123!")

        assert success is False
        user.refresh_from_db()
        assert user.check_password(old_password)
