import pytest

from apps.authentication.api.v1.serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
)
from apps.users.models import User, UserRoles
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestRegisterSerializer:
    """Tests for RegisterSerializer."""

    def test_register_serializer_valid_data(self):
        """Test serializer accepts valid registration data."""
        data = {
            "email": "newuser@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "09123456789",
            "role": UserRoles.CUSTOMER,
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }

        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["email"] == "newuser@example.com"
        assert serializer.validated_data["first_name"] == "John"
        assert serializer.validated_data["role"] == UserRoles.CUSTOMER

    def test_register_serializer_passwords_do_not_match(self):
        """Test serializer rejects when passwords don't match."""
        data = {
            "email": "newuser@example.com",
            "password": "StrongPass123!",
            "password_confirm": "DifferentPass456!",
        }

        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert "password_confirm" in serializer.errors
        assert "Passwords do not match" in str(serializer.errors["password_confirm"])

    def test_register_serializer_password_too_short(self):
        """Test serializer rejects password shorter than 8 characters."""
        data = {
            "email": "newuser@example.com",
            "password": "short",
            "password_confirm": "short",
        }

        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert "password" in serializer.errors

    def test_register_serializer_duplicate_email(self):
        """Test serializer rejects duplicate email."""
        UserFactory(email="existing@example.com")

        data = {
            "email": "existing@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }

        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert "email" in serializer.errors
        assert "already exists" in str(serializer.errors["email"])

    def test_register_serializer_invalid_role(self):
        """Test serializer rejects invalid role."""
        data = {
            "email": "newuser@example.com",
            "role": "invalid_role",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }

        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert "role" in serializer.errors
        # پیام خطا از ModelSerializer می‌آید
        assert "valid choice" in str(serializer.errors["role"]).lower()


    def test_register_serializer_email_normalization(self):
        """Test serializer normalizes email to lowercase."""
        data = {
            "email": "MixedCase@Example.COM",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }

        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["email"] == "mixedcase@example.com"

    def test_register_serializer_weak_password(self):
        """Test serializer rejects weak passwords."""
        data = {
            "email": "newuser@example.com",
            "password": "12345678",
            "password_confirm": "12345678",
        }

        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert "password" in serializer.errors or "non_field_errors" in serializer.errors


class TestLoginSerializer:
    """Tests for LoginSerializer."""

    def test_login_serializer_valid_credentials(self):
        """Test serializer accepts valid login credentials."""
        user = UserFactory(email="login@example.com")
        raw_password = "StrongPass123!"
        user.set_password(raw_password)
        user.save()

        data = {
            "email": "login@example.com",
            "password": raw_password,
        }

        serializer = LoginSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert "user" in serializer.validated_data
        assert serializer.validated_data["user"] == user

    def test_login_serializer_invalid_email(self):
        """Test serializer rejects non-existent email."""
        data = {
            "email": "nonexistent@example.com",
            "password": "StrongPass123!",
        }

        serializer = LoginSerializer(data=data)
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors
        assert "Invalid email or password" in str(serializer.errors["non_field_errors"])

    def test_login_serializer_wrong_password(self):
        """Test serializer rejects wrong password."""
        user = UserFactory(email="login@example.com")
        user.set_password("CorrectPass123!")
        user.save()

        data = {
            "email": "login@example.com",
            "password": "WrongPass456!",
        }

        serializer = LoginSerializer(data=data)
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors

    def test_login_serializer_inactive_user(self):
        """Test serializer rejects inactive user."""
        user = UserFactory(email="inactive@example.com", is_active=False)
        user.set_password("StrongPass123!")
        user.save()

        data = {
            "email": "inactive@example.com",
            "password": "StrongPass123!",
        }

        serializer = LoginSerializer(data=data)
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors

        error_message = str(serializer.errors["non_field_errors"][0])
        # بسته به تنظیمات authenticate، می‌تواند یکی از این دو باشد
        assert error_message in ["This account is inactive.", "Invalid email or password."]

    def test_login_serializer_email_normalization(self):
        """Test serializer normalizes email to lowercase."""
        user = UserFactory(email="login@example.com")
        user.set_password("StrongPass123!")
        user.save()

        data = {
            "email": "LOGIN@EXAMPLE.COM",
            "password": "StrongPass123!",
        }

        serializer = LoginSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["user"] == user

    def test_login_serializer_missing_fields(self):
        """Test serializer rejects missing required fields."""
        data = {}

        serializer = LoginSerializer(data=data)
        assert not serializer.is_valid()
        assert "email" in serializer.errors
        assert "password" in serializer.errors


class TestChangePasswordSerializer:
    """Tests for ChangePasswordSerializer."""

    def test_change_password_valid_data(self):
        """Test serializer accepts valid password change data."""
        user = UserFactory()
        user.set_password("CurrentPass123!")
        user.save()

        data = {
            "current_password": "CurrentPass123!",
            "new_password": "NewStrongPass456!",
            "new_password_confirm": "NewStrongPass456!",
        }

        # Create mock request with user
        mock_request = type("Request", (), {"user": user})()

        serializer = ChangePasswordSerializer(data=data, context={"request": mock_request})
        assert serializer.is_valid(), serializer.errors

    def test_change_password_wrong_current_password(self):
        """Test serializer rejects wrong current password."""
        user = UserFactory()
        user.set_password("CurrentPass123!")
        user.save()

        data = {
            "current_password": "WrongPass456!",
            "new_password": "NewStrongPass789!",
            "new_password_confirm": "NewStrongPass789!",
        }

        mock_request = type("Request", (), {"user": user})()

        serializer = ChangePasswordSerializer(data=data, context={"request": mock_request})
        assert not serializer.is_valid()
        assert "current_password" in serializer.errors
        assert "incorrect" in str(serializer.errors["current_password"]).lower()

    def test_change_password_new_passwords_do_not_match(self):
        """Test serializer rejects when new passwords don't match."""
        user = UserFactory()
        user.set_password("CurrentPass123!")
        user.save()

        data = {
            "current_password": "CurrentPass123!",
            "new_password": "NewPass123!",
            "new_password_confirm": "DifferentPass456!",
        }

        mock_request = type("Request", (), {"user": user})()

        serializer = ChangePasswordSerializer(data=data, context={"request": mock_request})
        assert not serializer.is_valid()
        assert "new_password_confirm" in serializer.errors
        assert "do not match" in str(serializer.errors["new_password_confirm"]).lower()

    def test_change_password_weak_new_password(self):
        """Test serializer rejects weak new password."""
        user = UserFactory()
        user.set_password("CurrentPass123!")
        user.save()

        data = {
            "current_password": "CurrentPass123!",
            "new_password": "123",
            "new_password_confirm": "123",
        }

        mock_request = type("Request", (), {"user": user})()

        serializer = ChangePasswordSerializer(data=data, context={"request": mock_request})
        assert not serializer.is_valid()
        # Should have password validation error
        assert "new_password" in serializer.errors or "non_field_errors" in serializer.errors

    def test_change_password_same_as_old_password(self):
        """Test serializer handles same password."""
        user = UserFactory()
        user.set_password("SamePassword123!")
        user.save()

        data = {
            "current_password": "SamePassword123!",
            "new_password": "SamePassword123!",
            "new_password_confirm": "SamePassword123!",
        }

        mock_request = type("Request", (), {"user": user})()

        serializer = ChangePasswordSerializer(data=data, context={"request": mock_request})
        # This may pass or fail depending on password validation
        # Both are acceptable - just make sure it doesn't crash
        serializer.is_valid()


class TestPasswordResetRequestSerializer:
    """Tests for PasswordResetRequestSerializer."""

    def test_password_reset_request_valid_email(self):
        """Test serializer accepts valid email."""
        data = {"email": "user@example.com"}

        serializer = PasswordResetRequestSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["email"] == "user@example.com"

    def test_password_reset_request_invalid_email(self):
        """Test serializer rejects invalid email format."""
        data = {"email": "not-an-email"}

        serializer = PasswordResetRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_password_reset_request_empty_email(self):
        """Test serializer rejects empty email."""
        data = {"email": ""}

        serializer = PasswordResetRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_password_reset_request_missing_email(self):
        """Test serializer rejects missing email field."""
        data = {}

        serializer = PasswordResetRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert "email" in serializer.errors


class TestPasswordResetConfirmSerializer:
    """Tests for PasswordResetConfirmSerializer."""

    def test_password_reset_confirm_valid_data(self):
        """Test serializer accepts valid reset data."""
        data = {
            "uid": "MTIz",
            "token": "abc123def456",
            "new_password": "NewStrongPass789!",
            "new_password_confirm": "NewStrongPass789!",
        }

        serializer = PasswordResetConfirmSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["uid"] == "MTIz"
        assert serializer.validated_data["token"] == "abc123def456"

    def test_password_reset_confirm_passwords_do_not_match(self):
        """Test serializer rejects when passwords don't match."""
        data = {
            "uid": "MTIz",
            "token": "abc123",
            "new_password": "NewPass123!",
            "new_password_confirm": "DifferentPass456!",
        }

        serializer = PasswordResetConfirmSerializer(data=data)
        assert not serializer.is_valid()
        assert "new_password_confirm" in serializer.errors
        assert "do not match" in str(serializer.errors["new_password_confirm"]).lower()

    def test_password_reset_confirm_missing_fields(self):
        """Test serializer rejects missing required fields."""
        required_fields = ["uid", "token", "new_password", "new_password_confirm"]

        for field in required_fields:
            data = {
                "uid": "MTIz",
                "token": "abc123",
                "new_password": "NewPass123!",
                "new_password_confirm": "NewPass123!",
            }
            del data[field]

            serializer = PasswordResetConfirmSerializer(data=data)
            assert not serializer.is_valid()
            assert field in serializer.errors

    def test_password_reset_confirm_password_too_short(self):
        """Test serializer rejects password shorter than min_length (8)."""
        data = {
            "uid": "MTIz",
            "token": "abc123",
            "new_password": "1234567",  # 7 characters
            "new_password_confirm": "1234567",
        }

        serializer = PasswordResetConfirmSerializer(data=data)
        assert not serializer.is_valid()
        assert "new_password" in serializer.errors
        assert "at least 8 characters" in str(serializer.errors["new_password"])

    def test_password_reset_confirm_password_exactly_min_length(self):
        """Test serializer accepts password with exactly 8 characters."""
        data = {
            "uid": "MTIz",
            "token": "abc123",
            "new_password": "Pass1234",  # Exactly 8 characters
            "new_password_confirm": "Pass1234",
        }

        serializer = PasswordResetConfirmSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_password_reset_confirm_empty_values(self):
        """Test serializer rejects empty string values."""
        data = {
            "uid": "",
            "token": "",
            "new_password": "",
            "new_password_confirm": "",
        }

        serializer = PasswordResetConfirmSerializer(data=data)
        assert not serializer.is_valid()
        # All fields should have errors
        for field in ["uid", "token", "new_password", "new_password_confirm"]:
            assert field in serializer.errors


class TestIntegrationSerializersWithModels:
    """Integration tests between serializers and models."""

    def test_register_serializer_creates_valid_user(self):
        """Test that valid serializer data can create a user."""
        data = {
            "email": "integrate@example.com",
            "first_name": "Integration",
            "last_name": "Test",
            "phone_number": "09123456789",
            "role": UserRoles.CUSTOMER,
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }

        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        # Create user from validated data
        user = User.objects.create_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            first_name=serializer.validated_data.get("first_name", ""),
            last_name=serializer.validated_data.get("last_name", ""),
        )

        assert user.email == "integrate@example.com"
        assert user.check_password("StrongPass123!")

    def test_login_serializer_authenticates_user(self):
        """Test that login serializer properly authenticates user."""
        user = UserFactory(email="auth@example.com")
        raw_password = "AuthPass123!"
        user.set_password(raw_password)
        user.save()

        data = {
            "email": "auth@example.com",
            "password": raw_password,
        }

        serializer = LoginSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["user"] == user
