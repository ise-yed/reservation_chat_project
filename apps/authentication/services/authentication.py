from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.services.otp import OTPService
from apps.notifications.events.dispatcher import publish_notification_event
from apps.notifications.events.event_types import NotificationEvent
from apps.users.models import User


@transaction.atomic
def register_user(*, email, password, first_name="", last_name="", phone_number="", role="customer"):
    """Register a new user account."""
    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        role=role,
    )
    return user


def build_auth_tokens_for_user(user):
    """Generate JWT access and refresh tokens for authenticated user."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def logout_user(refresh_token: str):
    """Blacklist the given refresh token."""
    token = RefreshToken(refresh_token)
    token.blacklist()


def request_password_reset_otp(*, email: str):
    """Generate and send OTP for password reset if user exists."""
    user = User.objects.filter(email__iexact=email, is_active=True).first()
    
    # We silently ignore non-existent emails to prevent user enumeration
    if user:
        code, error_msg = OTPService.create_otp(user.id, user.email, purpose="password_reset")
        if error_msg:
            return error_msg
        OTPService.send_otp_email(user, code, purpose_text="Password Reset")
    return None


@transaction.atomic
def reset_password_with_otp(*, email: str, code: str, new_password: str) -> tuple[bool, str]:
    """Verify OTP and reset password."""
    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if not user:
        return False, "Invalid request or expired OTP."

    is_valid, error_msg = OTPService.verify_otp(user.id, code, purpose="password_reset")
    if not is_valid:
        return False, error_msg

    user.set_password(new_password)
    user.save(update_fields=["password"])

    publish_notification_event(
        event_name=NotificationEvent.PASSWORD_CHANGED,
        recipient=user,
    )
    return True, ""


def request_password_change_otp(*, user):
    """Generate and send OTP for password change."""
    code, error_msg = OTPService.create_otp(user.id, user.email, purpose="password_change")
    if error_msg:
        return error_msg
    OTPService.send_otp_email(user, code, purpose_text="Password Change")
    return None


@transaction.atomic
def change_password_with_otp(*, user, code: str, new_password: str) -> tuple[bool, str]:
    """Verify OTP and change password for authenticated user."""
    is_valid, error_msg = OTPService.verify_otp(user.id, code, purpose="password_change")
    if not is_valid:
        return False, error_msg

    user.set_password(new_password)
    user.save(update_fields=["password"])

    publish_notification_event(
        event_name=NotificationEvent.PASSWORD_CHANGED,
        recipient=user,
    )
    return True, ""