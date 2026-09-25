from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView
from django.utils.translation import gettext_lazy as _

from apps.authentication.api.v1.docs import (
    login_schema,
    logout_schema,
    me_get_schema,
    me_patch_schema,
    password_change_confirm_schema,
    password_change_request_schema,
    password_reset_confirm_schema,
    password_reset_request_schema,
    register_schema,
    token_refresh_schema,
)
from apps.authentication.api.v1.serializers import (
    LoginSerializer,
    LogoutSerializer,
    PasswordChangeConfirmSerializer,
    PasswordChangeRequestSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
)
from apps.authentication.services import (
    build_auth_tokens_for_user,
    change_password_with_otp,
    logout_user,
    register_user,
    request_password_change_otp,
    request_password_reset_otp,
    reset_password_with_otp,
)
from apps.users.api.v1.serializers.users import UserReadSerializer, UserUpdateSerializer
from apps.users.enums import UserRoles


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    @register_schema
    def post(self, request):
        serializer = RegisterSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = register_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            first_name=serializer.validated_data.get("first_name", ""),
            last_name=serializer.validated_data.get("last_name", ""),
            phone_number=serializer.validated_data.get("phone_number", ""),
            role=UserRoles.CUSTOMER,
        )

        tokens = build_auth_tokens_for_user(user)

        return Response(
            {
                "message": _("User registered successfully."),
                "user": UserReadSerializer(user).data,
                "tokens": tokens,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    @login_schema
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        tokens = build_auth_tokens_for_user(user)

        return Response(
            {
                "message": _("Login successful."),
                "user": UserReadSerializer(user).data,
                "tokens": tokens,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @logout_schema
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            logout_user(refresh_token=serializer.validated_data["refresh"])
        except Exception:
            return Response(
                {"message": _("Token is invalid or already blacklisted.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"message": _("Successfully logged out.")}, status=status.HTTP_200_OK)


class RefreshTokenView(TokenRefreshView):
    @token_refresh_schema
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @me_get_schema
    def get(self, request):
        return Response(UserReadSerializer(request.user).data)

    @me_patch_schema
    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserReadSerializer(request.user).data)


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    @password_reset_request_schema
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].lower().strip()
        request_password_reset_otp(email=email)
        return Response(
            {"message": _("If an account with this email exists, an OTP has been sent.")},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset_confirm"

    @password_reset_confirm_schema
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        success, error_msg = reset_password_with_otp(
            email=serializer.validated_data["email"],
            code=serializer.validated_data["code"],
            new_password=serializer.validated_data["new_password"],
        )

        if not success:
            return Response({"message": error_msg}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": _("Password has been reset successfully.")}, status=status.HTTP_200_OK)


class PasswordChangeRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_change"

    @password_change_request_schema
    def post(self, request):
        serializer = PasswordChangeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        error_msg = request_password_change_otp(user=request.user)

        if error_msg:
            return Response({"message": error_msg}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        return Response(
            {"message": _("An OTP has been sent to your email to confirm password change.")},
            status=status.HTTP_200_OK,
        )


class PasswordChangeConfirmView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_change_confirm"

    @password_change_confirm_schema
    def post(self, request):
        serializer = PasswordChangeConfirmSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        success, error_msg = change_password_with_otp(
            user=request.user,
            code=serializer.validated_data["code"],
            new_password=serializer.validated_data["new_password"],
        )

        if not success:
            return Response({"message": error_msg}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": _("Password changed successfully.")}, status=status.HTTP_200_OK)
