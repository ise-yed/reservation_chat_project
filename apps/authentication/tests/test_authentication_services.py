from unittest.mock import patch

import pytest
from django.db import IntegrityError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.services import (
    build_auth_tokens_for_user,
    change_password_with_otp,
    logout_user,
    register_user,
    request_password_change_otp,
    request_password_reset_otp,
    reset_password_with_otp,
)
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestRegisterUser:
    """Tests for register_user function."""

    def test_register_user_success(self):
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
        assert user.role == "customer"
        assert user.check_password("SecurePass123!")
        assert user.is_active

    def test_register_user_minimal_data(self):
        user = register_user(email="minimal@example.com", password="SecurePass123!")

        assert user.email == "minimal@example.com"
        assert user.first_name == ""
        assert user.role == "customer"
        assert user.check_password("SecurePass123!")

    def test_register_user_duplicate_email(self):
        register_user(email="duplicate@example.com", password="Pass123!")

        with pytest.raises(IntegrityError):
            register_user(email="duplicate@example.com", password="Pass456!")


class TestBuildAuthTokensForUser:
    """Tests for build_auth_tokens_for_user function."""

    def test_build_auth_tokens_success(self):
        user = UserFactory()
        tokens = build_auth_tokens_for_user(user)

        assert "access" in tokens
        assert "refresh" in tokens
        assert isinstance(tokens["access"], str)
        assert len(tokens["access"]) > 0

    def test_tokens_are_different_for_different_users(self):
        user1 = UserFactory()
        user2 = UserFactory()

        tokens1 = build_auth_tokens_for_user(user1)
        tokens2 = build_auth_tokens_for_user(user2)

        assert tokens1["access"] != tokens2["access"]


class TestLogoutUser:
    """Tests for logout_user function."""

    def test_logout_user_success(self):
        user = UserFactory()
        refresh = RefreshToken.for_user(user)
        
        # Should execute without throwing errors and blacklist the token
        logout_user(str(refresh))


class TestPasswordResetServices:
    """Tests for password reset via OTP flow."""

    @patch("apps.authentication.services.authentication.OTPService.send_otp_email")
    @patch("apps.authentication.services.authentication.OTPService.create_otp")
    def test_request_password_reset_otp_success(self, mock_create, mock_send):
        user = UserFactory(email="reset@example.com")
        # create_otp returns (code, error_msg)
        mock_create.return_value = ("123456", None)

        error = request_password_reset_otp(email=user.email)
        
        assert error is None
        mock_create.assert_called_once_with(user.id, user.email, purpose="password_reset")
        mock_send.assert_called_once_with(user, "123456", purpose_text="Password Reset")

    def test_request_password_reset_otp_nonexistent_email(self):
        # Should silently return None to prevent email enumeration
        error = request_password_reset_otp(email="nonexistent@example.com")
        assert error is None

    @patch("apps.authentication.services.authentication.OTPService.verify_otp")
    @patch("apps.authentication.services.authentication.publish_notification_event")
    def test_reset_password_with_otp_success(self, mock_publish, mock_verify):
        user = UserFactory(email="reset@example.com")
        # verify_otp returns (is_valid, error_msg)
        mock_verify.return_value = (True, None)

        success, msg = reset_password_with_otp(
            email=user.email, code="123456", new_password="NewPass123!"
        )

        assert success is True
        user.refresh_from_db()
        assert user.check_password("NewPass123!")
        assert mock_publish.called

    @patch("apps.authentication.services.authentication.OTPService.verify_otp")
    def test_reset_password_with_otp_invalid_code(self, mock_verify):
        user = UserFactory(email="reset@example.com")
        old_password_hash = user.password
        mock_verify.return_value = (False, "Invalid code")

        success, msg = reset_password_with_otp(
            email=user.email, code="wrong", new_password="NewPass123!"
        )

        assert success is False
        assert msg == "Invalid code"
        user.refresh_from_db()
        assert user.password == old_password_hash

    def test_reset_password_with_otp_nonexistent_email(self):
        success, msg = reset_password_with_otp(
            email="nonexistent@example.com", code="123456", new_password="NewPass123!"
        )
        assert success is False
        assert "Invalid request" in msg


class TestPasswordChangeServices:
    """Tests for authenticated user password change via OTP flow."""

    @patch("apps.authentication.services.authentication.OTPService.send_otp_email")
    @patch("apps.authentication.services.authentication.OTPService.create_otp")
    def test_request_password_change_otp_success(self, mock_create, mock_send):
        user = UserFactory()
        mock_create.return_value = ("654321", None)

        error = request_password_change_otp(user=user)
        
        assert error is None
        mock_create.assert_called_once_with(user.id, user.email, purpose="password_change")
        mock_send.assert_called_once_with(user, "654321", purpose_text="Password Change")

    @patch("apps.authentication.services.authentication.OTPService.verify_otp")
    @patch("apps.authentication.services.authentication.publish_notification_event")
    def test_change_password_with_otp_success(self, mock_publish, mock_verify):
        user = UserFactory()
        mock_verify.return_value = (True, None)

        success, msg = change_password_with_otp(
            user=user, code="654321", new_password="BrandNewPass1!"
        )

        assert success is True
        user.refresh_from_db()
        assert user.check_password("BrandNewPass1!")
        assert mock_publish.called

    @patch("apps.authentication.services.authentication.OTPService.verify_otp")
    def test_change_password_with_otp_invalid_code(self, mock_verify):
        user = UserFactory()
        old_password_hash = user.password
        mock_verify.return_value = (False, "Expired code")

        success, msg = change_password_with_otp(
            user=user, code="000000", new_password="BrandNewPass1!"
        )

        assert success is False
        assert msg == "Expired code"
        user.refresh_from_db()
        assert user.password == old_password_hash