from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import transaction
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework_simplejwt.tokens import RefreshToken

from apps.notifications.events.dispatcher import publish_notification_event
from apps.notifications.events.event_types import NotificationEvent
from apps.users.models import User


@transaction.atomic
def register_user(
    *, email, password, first_name="", last_name="", phone_number="", role="customer"
):
    """
    Register a new user account.

    Creates a user with hashed password and returns the user instance.
    """
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


def request_password_reset(*, user):
    """
    Send password reset email to user.

    Generates reset token and publishes notification event.
    """
    reset_base_url = getattr(settings, "FRONTEND_PASSWORD_RESET_URL", None)

    if not reset_base_url:
        raise ImproperlyConfigured("FRONTEND_PASSWORD_RESET_URL must be configured.")

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    query_params = urlencode(
        {
            "uid": uid,
            "token": token,
        }
    )

    reset_link = f"{reset_base_url}?{query_params}"

    publish_notification_event(
        event_name=NotificationEvent.PASSWORD_RESET_REQUESTED,
        recipient=user,
        context={
            "reset_link": reset_link,
        },
        run_after_commit=True,
    )


@transaction.atomic
def change_password(*, user, new_password):
    """
    Change authenticated user's password.

    Updates password and publishes password changed notification.
    """
    user.set_password(new_password)
    user.save(update_fields=["password"])

    publish_notification_event(
        event_name=NotificationEvent.PASSWORD_CHANGED,
        recipient=user,
    )
    return user


@transaction.atomic
def reset_password(*, uid, token, new_password):
    """
    Reset user's password using valid reset token.

    Validates token and password strength, then updates password.
    Returns True if successful, False otherwise.
    """
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, User.DoesNotExist):
        return False

    if not default_token_generator.check_token(user, token):
        return False

    try:
        password_validation.validate_password(new_password, user)
    except ValidationError:
        return False

    user.set_password(new_password)
    user.save(update_fields=["password"])

    publish_notification_event(
        event_name=NotificationEvent.PASSWORD_CHANGED,
        recipient=user,
    )
    return True
