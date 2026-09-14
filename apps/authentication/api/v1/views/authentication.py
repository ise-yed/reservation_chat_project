from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView

from apps.authentication.api.v1.docs import (
    change_password_schema,
    login_schema,
    me_get_schema,
    me_patch_schema,
    password_reset_confirm_schema,
    password_reset_request_schema,
    register_schema,
    token_refresh_schema,
)
from apps.authentication.api.v1.serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
)
from apps.authentication.services import (
    build_auth_tokens_for_user,
    change_password,
    register_user,
    request_password_reset,
    reset_password,
)
from apps.users.api.v1.serializers.users import UserReadSerializer, UserUpdateSerializer
from apps.users.enums import UserRoles
from apps.users.models import User


class RegisterView(APIView):
    """Register a new user and return the authenticated user with JWT tokens."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"
    @register_schema
    def post(self, request):
        """Create a new user account."""
        serializer = RegisterSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = register_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            first_name=serializer.validated_data.get("first_name", ""),
            last_name=serializer.validated_data.get("last_name", ""),
            phone_number=serializer.validated_data.get("phone_number", ""),
            role=serializer.validated_data.get("role", UserRoles.CUSTOMER),
        )

        tokens = build_auth_tokens_for_user(user)

        return Response(
            {
                "message": "User registered successfully.",
                "user": UserReadSerializer(user).data,
                "tokens": tokens,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Authenticate a user and return JWT tokens."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    @login_schema
    def post(self, request):
        """Authenticate a user using email and password."""
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        tokens = build_auth_tokens_for_user(user)

        return Response(
            {
                "message": "Login successful.",
                "user": UserReadSerializer(user).data,
                "tokens": tokens,
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """Retrieve or partially update the authenticated user's profile."""

    permission_classes = [permissions.IsAuthenticated]

    @me_get_schema
    def get(self, request):
        """Return the authenticated user's profile."""
        return Response(UserReadSerializer(request.user).data)

    @me_patch_schema
    def patch(self, request):
        """Partially update the authenticated user's profile."""
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(UserReadSerializer(request.user).data)


class ChangePasswordView(APIView):
    """Change the authenticated user's password."""

    permission_classes = [permissions.IsAuthenticated]

    @change_password_schema
    def post(self, request):
        """Update the authenticated user's password after validating the current password."""
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        change_password(
            user=request.user,
            new_password=serializer.validated_data["new_password"],
        )

        return Response(
            {"message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )


class PasswordResetRequestView(APIView):
    """Send a password reset email if the submitted email belongs to an active user."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"
    @password_reset_request_schema
    def post(self, request):
        """Request a password reset link."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].lower().strip()
        user = User.objects.filter(email__iexact=email, is_active=True).first()

        if user:
            request_password_reset(user=user)

        return Response(
            {
                "message": (
                    "If an account with this email exists, a password reset link has been sent."
                )
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """Reset a user's password using a valid password reset token."""

    permission_classes = [permissions.AllowAny]

    @password_reset_confirm_schema
    def post(self, request):
        """Confirm a password reset request and set the new password."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        success = reset_password(
            uid=serializer.validated_data["uid"],
            token=serializer.validated_data["token"],
            new_password=serializer.validated_data["new_password"],
        )

        if not success:
            return Response(
                {"message": "Invalid or expired reset token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )


class RefreshTokenView(TokenRefreshView):
    """Refresh an access token using a valid refresh token."""

    @token_refresh_schema
    def post(self, request, *args, **kwargs):
        """Return a new access token for a valid refresh token."""
        return super().post(request, *args, **kwargs)
