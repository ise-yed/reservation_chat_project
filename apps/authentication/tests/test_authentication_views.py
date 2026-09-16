from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.authentication.services import build_auth_tokens_for_user
from apps.users.models import User, UserRoles
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestRegisterView:
    """Tests for RegisterView."""

    def test_register_user_success(self):
        """Test successful user registration."""
        client = APIClient()
        url = reverse("authentication:register")

        payload = {
            "email": "newuser@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "09123456789",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert "message" in response.data
        assert "user" in response.data
        assert "tokens" in response.data

        assert User.objects.filter(email="newuser@example.com").exists()

    def test_register_user_missing_fields(self):
        """Test registration fails with missing required fields."""
        client = APIClient()
        url = reverse("authentication:register")

        payload = {
            "email": "newuser@example.com",
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "errors" in response.data
        assert "password" in response.data["errors"]

    def test_register_user_passwords_do_not_match(self):
        """Test registration fails when passwords don't match."""
        client = APIClient()
        url = reverse("authentication:register")

        payload = {
            "email": "newuser@example.com",
            "password": "StrongPass123!",
            "password_confirm": "DifferentPass456!",
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "errors" in response.data
        assert "password_confirm" in response.data["errors"]

    def test_register_user_duplicate_email(self):
        """Test registration fails with duplicate email."""
        UserFactory(email="existing@example.com")

        client = APIClient()
        url = reverse("authentication:register")

        payload = {
            "email": "existing@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "errors" in response.data
        assert "email" in response.data["errors"]

    def test_register_user_ignores_role_field(self):
        """Test registration ignores role field completely and forces CUSTOMER role."""
        client = APIClient()
        url = reverse("authentication:register")

        payload = {
            "email": "newuser@example.com",
            "role": "provider",  # Should be dropped silently
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }

        response = client.post(url, payload, format="json")

        # Because role is ignored, the request should be successful and create a CUSTOMER
        assert response.status_code == status.HTTP_201_CREATED

        user = User.objects.get(email="newuser@example.com")
        assert user.role == UserRoles.CUSTOMER

    def test_register_user_weak_password(self):
        """Test registration fails with weak password."""
        client = APIClient()
        url = reverse("authentication:register")

        payload = {
            "email": "newuser@example.com",
            "password": "123",
            "password_confirm": "123",
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "errors" in response.data
        assert (
            "password" in response.data["errors"] or "password_confirm" in response.data["errors"]
        )


class TestLoginView:
    """Tests for LoginView."""

    def test_login_success(self):
        """Test successful login with valid credentials."""
        user = UserFactory(email="login@example.com")
        password = "StrongPass123!"
        user.set_password(password)
        user.save()

        client = APIClient()
        url = reverse("authentication:login")

        payload = {
            "email": "login@example.com",
            "password": password,
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "tokens" in response.data
        assert response.data["user"]["email"] == "login@example.com"

    def test_login_invalid_email(self):
        """Test login fails with non-existent email."""
        client = APIClient()
        url = reverse("authentication:login")

        payload = {
            "email": "nonexistent@example.com",
            "password": "StrongPass123!",
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "errors" in response.data
        assert "non_field_errors" in response.data["errors"]

    def test_login_wrong_password(self):
        """Test login fails with wrong password."""
        user = UserFactory(email="login@example.com")
        user.set_password("CorrectPass123!")
        user.save()

        client = APIClient()
        url = reverse("authentication:login")

        payload = {
            "email": "login@example.com",
            "password": "WrongPass456!",
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "errors" in response.data
        assert "non_field_errors" in response.data["errors"]

    def test_login_inactive_user(self):
        """Test login fails for inactive user."""
        user = UserFactory(email="inactive@example.com", is_active=False)
        user.set_password("StrongPass123!")
        user.save()

        client = APIClient()
        url = reverse("authentication:login")

        payload = {
            "email": "inactive@example.com",
            "password": "StrongPass123!",
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "errors" in response.data

    def test_login_missing_fields(self):
        """Test login fails with missing fields."""
        client = APIClient()
        url = reverse("authentication:login")

        response = client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "errors" in response.data
        assert "email" in response.data["errors"]
        assert "password" in response.data["errors"]


class TestMeView:
    """Tests for MeView."""

    def test_get_profile_success(self):
        """Test getting authenticated user's profile."""
        user = UserFactory()

        client = APIClient()
        client.force_authenticate(user=user)
        url = reverse("authentication:me")

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email

    def test_get_profile_unauthenticated(self):
        """Test getting profile fails without authentication."""
        client = APIClient()
        url = reverse("authentication:me")

        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile_success(self):
        """Test partially updating user profile."""
        user = UserFactory(first_name="Old", last_name="Name")

        client = APIClient()
        client.force_authenticate(user=user)
        url = reverse("authentication:me")

        payload = {
            "first_name": "New",
            "last_name": "Name",
        }

        response = client.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "New"

        user.refresh_from_db()
        assert user.first_name == "New"

    def test_update_profile_unauthenticated(self):
        """Test updating profile fails without authentication."""
        client = APIClient()
        url = reverse("authentication:me")

        payload = {"first_name": "New"}

        response = client.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile_invalid_data(self):
        """Test updating profile with invalid data."""
        user = UserFactory()

        client = APIClient()
        client.force_authenticate(user=user)
        url = reverse("authentication:me")

        payload = {"email": "not-an-email"}

        response = client.patch(url, payload, format="json")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]


class TestChangePasswordView:
    """Tests for ChangePasswordView."""

    def test_change_password_success(self):
        """Test successful password change."""
        user = UserFactory()
        user.set_password("OldPass123!")
        user.save()

        client = APIClient()
        client.force_authenticate(user=user)
        url = reverse("authentication:change_password")

        payload = {
            "current_password": "OldPass123!",
            "new_password": "NewStrongPass456!",
            "new_password_confirm": "NewStrongPass456!",
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.check_password("NewStrongPass456!")

    def test_change_password_wrong_current_password(self):
        """Test password change fails with wrong current password."""
        user = UserFactory()
        user.set_password("OldPass123!")
        user.save()

        client = APIClient()
        client.force_authenticate(user=user)
        url = reverse("authentication:change_password")

        payload = {
            "current_password": "WrongPass456!",
            "new_password": "NewStrongPass789!",
            "new_password_confirm": "NewStrongPass789!",
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "errors" in response.data
        assert "current_password" in response.data["errors"]

    def test_change_password_new_passwords_do_not_match(self):
        """Test password change fails when new passwords don't match."""
        user = UserFactory()
        user.set_password("OldPass123!")
        user.save()

        client = APIClient()
        client.force_authenticate(user=user)
        url = reverse("authentication:change_password")

        payload = {
            "current_password": "OldPass123!",
            "new_password": "NewPass123!",
            "new_password_confirm": "DifferentPass456!",
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "errors" in response.data
        assert "new_password_confirm" in response.data["errors"]

    def test_change_password_unauthenticated(self):
        """Test password change fails without authentication."""
        client = APIClient()
        url = reverse("authentication:change_password")

        payload = {
            "current_password": "OldPass123!",
            "new_password": "NewPass123!",
            "new_password_confirm": "NewPass123!",
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPasswordResetRequestView:
    """Tests for PasswordResetRequestView."""

    @patch("apps.authentication.api.v1.views.authentication.request_password_reset")
    def test_password_reset_request_success(self, mock_send_email):
        """Test successful password reset request."""
        user = UserFactory(email="reset@example.com", is_active=True)

        client = APIClient()
        url = reverse("authentication:password_reset")

        payload = {"email": "reset@example.com"}

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        mock_send_email.assert_called_once_with(user=user)

    @patch("apps.authentication.services.request_password_reset")
    def test_password_reset_request_nonexistent_email(self, mock_send_email):
        """Test password reset request with non-existent email."""
        client = APIClient()
        url = reverse("authentication:password_reset")

        payload = {"email": "nonexistent@example.com"}

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        mock_send_email.assert_not_called()

    def test_password_reset_request_invalid_email(self):
        """Test password reset request with invalid email format."""
        client = APIClient()
        url = reverse("authentication:password_reset")

        payload = {"email": "not-an-email"}

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "errors" in response.data
        assert "email" in response.data["errors"]


class TestPasswordResetConfirmView:
    """Tests for PasswordResetConfirmView."""

    def test_password_reset_confirm_success(self):
        """Test successful password reset confirmation."""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        user = UserFactory()
        user.set_password("OldPass123!")
        user.save()

        uid = urlsafe_base64_encode(force_bytes(str(user.pk)))
        token = default_token_generator.make_token(user)

        client = APIClient()
        url = reverse("authentication:password_reset_confirm")

        payload = {
            "uid": uid,
            "token": token,
            "new_password": "NewResetPass789!",
            "new_password_confirm": "NewResetPass789!",
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK

    def test_password_reset_confirm_invalid_token(self):
        """Test password reset fails with invalid token."""
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        user = UserFactory()
        user.set_password("OldPass123!")
        user.save()

        uid = urlsafe_base64_encode(force_bytes(str(user.pk)))

        client = APIClient()
        url = reverse("authentication:password_reset_confirm")

        payload = {
            "uid": uid,
            "token": "invalid-token",
            "new_password": "NewPass123!",
            "new_password_confirm": "NewPass123!",
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "message" in response.data

    def test_password_reset_confirm_passwords_do_not_match(self):
        """Test password reset fails when passwords don't match."""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        user = UserFactory()
        uid = urlsafe_base64_encode(force_bytes(str(user.pk)))
        token = default_token_generator.make_token(user)

        client = APIClient()
        url = reverse("authentication:password_reset_confirm")

        payload = {
            "uid": uid,
            "token": token,
            "new_password": "NewPass123!",
            "new_password_confirm": "DifferentPass456!",
        }

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "errors" in response.data
        assert "new_password_confirm" in response.data["errors"]


class TestRefreshTokenView:
    """Tests for RefreshTokenView."""

    def test_refresh_token_success(self):
        """Test successful token refresh."""
        user = UserFactory()
        tokens = build_auth_tokens_for_user(user)

        client = APIClient()
        url = reverse("authentication:auth-token-refresh")

        payload = {"refresh": tokens["refresh"]}

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_refresh_token_invalid(self):
        """Test refresh fails with invalid refresh token."""
        client = APIClient()
        url = reverse("authentication:auth-token-refresh")

        payload = {"refresh": "invalid-token"}

        response = client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token_missing(self):
        """Test refresh fails without refresh token."""
        client = APIClient()
        url = reverse("authentication:auth-token-refresh")

        response = client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "errors" in response.data
        assert "refresh" in response.data["errors"]


class TestAuthenticationFlow:
    """Integration tests for complete authentication flow."""

    def test_complete_auth_flow(self):
        """Test complete authentication flow: register -> login -> me -> change password."""
        client = APIClient()

        # 1. Register
        register_url = reverse("authentication:register")
        register_payload = {
            "email": "flow@example.com",
            "password": "FlowPass123!",
            "password_confirm": "FlowPass123!",
        }
        register_response = client.post(register_url, register_payload, format="json")
        assert register_response.status_code == status.HTTP_201_CREATED
        access_token = register_response.data["tokens"]["access"]

        # 2. Get profile with token
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        me_url = reverse("authentication:me")
        me_response = client.get(me_url)
        assert me_response.status_code == status.HTTP_200_OK
        assert me_response.data["email"] == "flow@example.com"

        # 3. Change password
        change_password_url = reverse("authentication:change_password")
        change_password_payload = {
            "current_password": "FlowPass123!",
            "new_password": "NewFlowPass456!",
            "new_password_confirm": "NewFlowPass456!",
        }
        change_response = client.post(change_password_url, change_password_payload, format="json")
        assert change_response.status_code == status.HTTP_200_OK

        # 4. Login with new password
        client.credentials()  # Clear credentials
        login_url = reverse("authentication:login")
        login_payload = {
            "email": "flow@example.com",
            "password": "NewFlowPass456!",
        }
        login_response = client.post(login_url, login_payload, format="json")
        assert login_response.status_code == status.HTTP_200_OK
