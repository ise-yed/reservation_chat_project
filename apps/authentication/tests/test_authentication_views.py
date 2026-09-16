from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import User, UserRoles
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestRegisterView:
    def test_register_user_success(self):
        client = APIClient()
        url = reverse("authentication:register")
        payload = {"email": "newuser@example.com", "password": "StrongPass123!", "password_confirm": "StrongPass123!"}
        response = client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_register_user_missing_fields(self):
        client = APIClient()
        response = client.post(reverse("authentication:register"), {"email": "newuser@example.com"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_user_passwords_do_not_match(self):
        client = APIClient()
        payload = {"email": "newuser@example.com", "password": "StrongPass123!", "password_confirm": "DiffPass123!"}
        response = client.post(reverse("authentication:register"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_user_duplicate_email(self):
        UserFactory(email="existing@example.com")
        client = APIClient()
        payload = {"email": "existing@example.com", "password": "StrongPass123!", "password_confirm": "StrongPass123!"}
        response = client.post(reverse("authentication:register"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_user_ignores_role_field(self):
        client = APIClient()
        payload = {"email": "newuser@example.com", "role": "provider", "password": "StrongPass123!", "password_confirm": "StrongPass123!"}
        response = client.post(reverse("authentication:register"), payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email="newuser@example.com")
        assert user.role == UserRoles.CUSTOMER

    def test_register_user_weak_password(self):
        client = APIClient()
        payload = {"email": "newuser@example.com", "password": "123", "password_confirm": "123"}
        response = client.post(reverse("authentication:register"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestLoginView:
    def test_login_success(self):
        user = UserFactory(email="login@example.com")
        user.set_password("StrongPass123!")
        user.save()
        client = APIClient()
        response = client.post(reverse("authentication:login"), {"email": "login@example.com", "password": "StrongPass123!"}, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_login_invalid_email(self):
        client = APIClient()
        response = client.post(reverse("authentication:login"), {"email": "nonexistent@example.com", "password": "123"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_wrong_password(self):
        user = UserFactory(email="login@example.com")
        user.set_password("CorrectPass123!")
        user.save()
        client = APIClient()
        response = client.post(reverse("authentication:login"), {"email": "login@example.com", "password": "WrongPass456!"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_inactive_user(self):
        user = UserFactory(email="inactive@example.com", is_active=False)
        user.set_password("StrongPass123!")
        user.save()
        client = APIClient()
        response = client.post(reverse("authentication:login"), {"email": "inactive@example.com", "password": "StrongPass123!"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_missing_fields(self):
        client = APIClient()
        response = client.post(reverse("authentication:login"), {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestMeView:
    def test_get_profile_success(self):
        user = UserFactory()
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(reverse("authentication:me"))
        assert response.status_code == status.HTTP_200_OK

    def test_get_profile_unauthenticated(self):
        client = APIClient()
        response = client.get(reverse("authentication:me"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile_success(self):
        user = UserFactory(first_name="Old")
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.patch(reverse("authentication:me"), {"first_name": "New"}, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_update_profile_unauthenticated(self):
        client = APIClient()
        response = client.patch(reverse("authentication:me"), {"first_name": "New"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestChangePasswordView:
    @patch("apps.authentication.api.v1.views.authentication.change_password_with_otp")
    def test_change_password_success(self, mock_change):
        mock_change.return_value = (True, "")
        user = UserFactory()
        user.set_password("OldPass123!")
        user.save()
        client = APIClient()
        client.force_authenticate(user=user)
        payload = {"current_password": "OldPass123!", "code": "123456", "new_password": "NewStrongPass456!", "new_password_confirm": "NewStrongPass456!"}
        response = client.post(reverse("authentication:password_change_confirm"), payload, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_change_password_wrong_current_password(self):
        user = UserFactory()
        user.set_password("OldPass123!")
        user.save()
        client = APIClient()
        client.force_authenticate(user=user)
        payload = {"current_password": "WrongPass456!", "code": "123456", "new_password": "NewStrongPass789!", "new_password_confirm": "NewStrongPass789!"}
        response = client.post(reverse("authentication:password_change_confirm"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_new_passwords_do_not_match(self):
        user = UserFactory()
        user.set_password("OldPass123!")
        user.save()
        client = APIClient()
        client.force_authenticate(user=user)
        payload = {"current_password": "OldPass123!", "code": "123456", "new_password": "NewPass123!", "new_password_confirm": "DifferentPass456!"}
        response = client.post(reverse("authentication:password_change_confirm"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestPasswordResetViews:
    @patch("apps.authentication.api.v1.views.authentication.request_password_reset_otp")
    def test_password_reset_request_success(self, mock_request_otp):
        mock_request_otp.return_value = None
        user = UserFactory(email="reset@example.com")
        client = APIClient()
        response = client.post(reverse("authentication:password_reset_request"), {"email": "reset@example.com"}, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_password_reset_request_invalid_email(self):
        client = APIClient()
        response = client.post(reverse("authentication:password_reset_request"), {"email": "not-an-email"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("apps.authentication.api.v1.views.authentication.reset_password_with_otp")
    def test_password_reset_confirm_success(self, mock_reset):
        mock_reset.return_value = (True, "")
        client = APIClient()
        payload = {"email": "user@example.com", "code": "123456", "new_password": "NewResetPass789!", "new_password_confirm": "NewResetPass789!"}
        response = client.post(reverse("authentication:password_reset_confirm"), payload, format="json")
        assert response.status_code == status.HTTP_200_OK

    @patch("apps.authentication.api.v1.views.authentication.reset_password_with_otp")
    def test_password_reset_confirm_invalid_token(self, mock_reset):
        mock_reset.return_value = (False, "Invalid code")
        client = APIClient()
        payload = {"email": "user@example.com", "code": "invalid", "new_password": "NewPass123!", "new_password_confirm": "NewPass123!"}
        response = client.post(reverse("authentication:password_reset_confirm"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_reset_confirm_passwords_do_not_match(self):
        client = APIClient()
        payload = {"email": "user@example.com", "code": "123456", "new_password": "NewPass123!", "new_password_confirm": "DifferentPass456!"}
        response = client.post(reverse("authentication:password_reset_confirm"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestAuthenticationFlow:
    def test_complete_auth_flow(self):
        client = APIClient()
        # 1. Register
        register_payload = {"email": "flow@example.com", "password": "FlowPass123!", "password_confirm": "FlowPass123!"}
        reg_response = client.post(reverse("authentication:register"), register_payload, format="json")
        assert reg_response.status_code == status.HTTP_201_CREATED
        
        # 2. Login
        client.credentials() 
        login_payload = {"email": "flow@example.com", "password": "FlowPass123!"}
        login_response = client.post(reverse("authentication:login"), login_payload, format="json")
        assert login_response.status_code == status.HTTP_200_OK