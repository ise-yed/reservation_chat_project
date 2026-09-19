import pytest

from apps.authentication.api.v1.serializers import (
    LoginSerializer,
    PasswordChangeConfirmSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
)
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestRegisterSerializer:
    def test_register_serializer_valid_data(self):
        data = {
            "email": "newuser@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "09123456789",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert "role" not in serializer.validated_data

    def test_register_serializer_passwords_do_not_match(self):
        data = {"email": "newuser@example.com", "password": "StrongPass123!", "password_confirm": "DifferentPass456!"}
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()

    def test_register_serializer_password_too_short(self):
        data = {"email": "newuser@example.com", "password": "short", "password_confirm": "short"}
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()

    def test_register_serializer_duplicate_email(self):
        UserFactory(email="existing@example.com")
        data = {"email": "existing@example.com", "password": "StrongPass123!", "password_confirm": "StrongPass123!"}
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()

    def test_register_serializer_ignores_role_field(self):
        data = {"email": "newuser@example.com", "role": "provider", "password": "StrongPass123!", "password_confirm": "StrongPass123!"}
        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid()
        assert "role" not in serializer.validated_data

    def test_register_serializer_email_normalization(self):
        data = {"email": "MixedCase@Example.COM", "password": "StrongPass123!", "password_confirm": "StrongPass123!"}
        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["email"] == "mixedcase@example.com"

    def test_register_serializer_weak_password(self):
        data = {"email": "newuser@example.com", "password": "12345678", "password_confirm": "12345678"}
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()


class TestLoginSerializer:
    def test_login_serializer_authenticates_user(self):
        user = UserFactory(email="auth@example.com")
        user.set_password("AuthPass123!")
        user.save()
        serializer = LoginSerializer(data={"email": "auth@example.com", "password": "AuthPass123!"})
        assert serializer.is_valid()
        assert serializer.validated_data["user"] == user

    def test_login_serializer_valid_credentials(self):
        user = UserFactory(email="login@example.com")
        user.set_password("StrongPass123!")
        user.save()
        serializer = LoginSerializer(data={"email": "login@example.com", "password": "StrongPass123!"})
        assert serializer.is_valid()

    def test_login_serializer_invalid_email(self):
        serializer = LoginSerializer(data={"email": "nonexistent@example.com", "password": "StrongPass123!"})
        assert not serializer.is_valid()

    def test_login_serializer_wrong_password(self):
        user = UserFactory(email="login@example.com")
        user.set_password("CorrectPass123!")
        user.save()
        serializer = LoginSerializer(data={"email": "login@example.com", "password": "WrongPass456!"})
        assert not serializer.is_valid()

    def test_login_serializer_inactive_user(self):
        user = UserFactory(email="inactive@example.com", is_active=False)
        user.set_password("StrongPass123!")
        user.save()
        serializer = LoginSerializer(data={"email": "inactive@example.com", "password": "StrongPass123!"})
        assert not serializer.is_valid()

    def test_login_serializer_email_normalization(self):
        user = UserFactory(email="login@example.com")
        user.set_password("StrongPass123!")
        user.save()
        serializer = LoginSerializer(data={"email": "LOGIN@EXAMPLE.COM", "password": "StrongPass123!"})
        assert serializer.is_valid()

    def test_login_serializer_missing_fields(self):
        serializer = LoginSerializer(data={})
        assert not serializer.is_valid()


class TestPasswordChangeConfirmSerializer:
    def test_change_password_valid_data(self):
        user = UserFactory()
        user.set_password("CurrentPass123!")
        user.save()
        data = {"current_password": "CurrentPass123!", "code": "123456", "new_password": "NewStrongPass456!", "new_password_confirm": "NewStrongPass456!"}
        mock_request = type("Request", (), {"user": user})()
        serializer = PasswordChangeConfirmSerializer(data=data, context={"request": mock_request})
        assert serializer.is_valid()

    def test_change_password_wrong_current_password(self):
        user = UserFactory()
        user.set_password("CurrentPass123!")
        user.save()
        data = {"current_password": "WrongPass456!", "code": "123456", "new_password": "NewStrongPass789!", "new_password_confirm": "NewStrongPass789!"}
        mock_request = type("Request", (), {"user": user})()
        serializer = PasswordChangeConfirmSerializer(data=data, context={"request": mock_request})
        assert not serializer.is_valid()

    def test_change_password_new_passwords_do_not_match(self):
        user = UserFactory()
        user.set_password("CurrentPass123!")
        user.save()
        data = {"current_password": "CurrentPass123!", "code": "123456", "new_password": "NewPass123!", "new_password_confirm": "DifferentPass456!"}
        mock_request = type("Request", (), {"user": user})()
        serializer = PasswordChangeConfirmSerializer(data=data, context={"request": mock_request})
        assert not serializer.is_valid()

    def test_change_password_weak_new_password(self):
        user = UserFactory()
        user.set_password("CurrentPass123!")
        user.save()
        data = {"current_password": "CurrentPass123!", "code": "123456", "new_password": "123", "new_password_confirm": "123"}
        mock_request = type("Request", (), {"user": user})()
        serializer = PasswordChangeConfirmSerializer(data=data, context={"request": mock_request})
        assert not serializer.is_valid()


class TestPasswordResetRequestSerializer:
    def test_password_reset_request_valid_email(self):
        serializer = PasswordResetRequestSerializer(data={"email": "user@example.com"})
        assert serializer.is_valid()

    def test_password_reset_request_invalid_email(self):
        serializer = PasswordResetRequestSerializer(data={"email": "not-an-email"})
        assert not serializer.is_valid()

    def test_password_reset_request_empty_email(self):
        serializer = PasswordResetRequestSerializer(data={"email": ""})
        assert not serializer.is_valid()

    def test_password_reset_request_missing_email(self):
        serializer = PasswordResetRequestSerializer(data={})
        assert not serializer.is_valid()


class TestPasswordResetConfirmSerializer:
    def test_password_reset_confirm_valid_data(self):
        data = {"email": "user@example.com", "code": "123456", "new_password": "NewStrongPass789!", "new_password_confirm": "NewStrongPass789!"}
        serializer = PasswordResetConfirmSerializer(data=data)
        assert serializer.is_valid()

    def test_password_reset_confirm_passwords_do_not_match(self):
        data = {"email": "user@example.com", "code": "123456", "new_password": "NewPass123!", "new_password_confirm": "DifferentPass456!"}
        serializer = PasswordResetConfirmSerializer(data=data)
        assert not serializer.is_valid()

    def test_password_reset_confirm_missing_fields(self):
        required_fields = ["email", "code", "new_password", "new_password_confirm"]
        for field in required_fields:
            data = {"email": "user@example.com", "code": "123456", "new_password": "NewPass123!", "new_password_confirm": "NewPass123!"}
            del data[field]
            serializer = PasswordResetConfirmSerializer(data=data)
            assert not serializer.is_valid()

    def test_password_reset_confirm_password_too_short(self):
        data = {"email": "user@example.com", "code": "123456", "new_password": "1234567", "new_password_confirm": "1234567"}
        serializer = PasswordResetConfirmSerializer(data=data)
        assert not serializer.is_valid()

    def test_password_reset_confirm_empty_values(self):
        data = {"email": "", "code": "", "new_password": "", "new_password_confirm": ""}
        serializer = PasswordResetConfirmSerializer(data=data)
        assert not serializer.is_valid()
