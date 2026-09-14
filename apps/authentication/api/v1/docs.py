from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from apps.authentication.api.v1.serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
)
from apps.users.api.v1.serializers import UserReadSerializer, UserUpdateSerializer


class TokenPairSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()


class AuthResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    user = UserReadSerializer()
    tokens = TokenPairSerializer()


class MessageResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


class AccessTokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()


register_schema = extend_schema(
    request=RegisterSerializer,
    responses={
        201: AuthResponseSerializer,
        400: OpenApiResponse(description="Invalid registration data."),
    },
    tags=["Authentication"],
)

login_schema = extend_schema(
    request=LoginSerializer,
    responses={
        200: AuthResponseSerializer,
        400: OpenApiResponse(description="Invalid login credentials."),
    },
    tags=["Authentication"],
)

me_get_schema = extend_schema(
    responses={
        200: UserReadSerializer,
        401: OpenApiResponse(description="Authentication credentials were not provided."),
    },
    tags=["Authentication"],
)

me_patch_schema = extend_schema(
    request=UserUpdateSerializer,
    responses={
        200: UserReadSerializer,
        400: OpenApiResponse(description="Invalid profile update data."),
        401: OpenApiResponse(description="Authentication credentials were not provided."),
    },
    tags=["Authentication"],
)

change_password_schema = extend_schema(
    request=ChangePasswordSerializer,
    responses={
        200: MessageResponseSerializer,
        400: OpenApiResponse(description="Invalid password change data."),
        401: OpenApiResponse(description="Authentication credentials were not provided."),
    },
    tags=["Authentication"],
)

password_reset_request_schema = extend_schema(
    request=PasswordResetRequestSerializer,
    responses={
        200: MessageResponseSerializer,
        400: OpenApiResponse(description="Invalid password reset request data."),
    },
    tags=["Authentication"],
)

password_reset_confirm_schema = extend_schema(
    request=PasswordResetConfirmSerializer,
    responses={
        200: MessageResponseSerializer,
        400: OpenApiResponse(description="Invalid or expired reset token."),
    },
    tags=["Authentication"],
)

token_refresh_schema = extend_schema(
    request=TokenRefreshSerializer,
    responses={
        200: AccessTokenResponseSerializer,
        401: OpenApiResponse(description="Refresh token is invalid or expired."),
    },
    tags=["Authentication"],
)
