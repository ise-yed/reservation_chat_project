from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from apps.authentication.api.v1.serializers import (
    LoginSerializer,
    LogoutSerializer,
    PasswordChangeConfirmSerializer,
    PasswordChangeRequestSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
)
from apps.users.api.v1.serializers.users import UserReadSerializer, UserUpdateSerializer

register_schema = extend_schema(
    summary="Register a new user",
    request=RegisterSerializer,
    responses={201: OpenApiResponse(description="User registered successfully.")},
)

login_schema = extend_schema(
    summary="Login with email and password",
    request=LoginSerializer,
    responses={200: OpenApiResponse(description="Login successful.")},
)

logout_schema = extend_schema(
    summary="Logout and blacklist refresh token",
    request=LogoutSerializer,
    responses={200: OpenApiResponse(description="Successfully logged out.")},
)

token_refresh_schema = extend_schema(
    summary="Refresh JWT token",
    request=TokenRefreshSerializer,
    responses={200: OpenApiResponse(description="Token refreshed.")},
)

me_get_schema = extend_schema(
    summary="Get current user profile",
    responses={200: UserReadSerializer},
)

me_patch_schema = extend_schema(
    summary="Update current user profile",
    request=UserUpdateSerializer,
    responses={200: UserReadSerializer},
)

password_reset_request_schema = extend_schema(
    summary="Request OTP for password reset",
    request=PasswordResetRequestSerializer,
    responses={200: OpenApiResponse(description="OTP sent if email exists.")},
)

password_reset_confirm_schema = extend_schema(
    summary="Confirm password reset with OTP",
    request=PasswordResetConfirmSerializer,
    responses={200: OpenApiResponse(description="Password reset successfully.")},
)

password_change_request_schema = extend_schema(
    summary="Request OTP for password change",
    request=PasswordChangeRequestSerializer,
    responses={200: OpenApiResponse(description="OTP sent.")},
)

password_change_confirm_schema = extend_schema(
    summary="Confirm password change with OTP",
    request=PasswordChangeConfirmSerializer,
    responses={200: OpenApiResponse(description="Password changed successfully.")},
)
