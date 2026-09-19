from typing import Any

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.validators import validate_email

from apps.notifications.enums import NotificationChannel, NotificationDeliveryStatus
from apps.notifications.events.registry import get_notification_event_config
from apps.notifications.models import NotificationDelivery
from apps.notifications.services import (
    create_notification,
    enqueue_notification_delivery,
    send_email_notification,
)


def handle_notification_event(
    *,
    event_name: str,
    recipient,
    context: dict[str, Any] | None = None,
) -> None:
    context = _build_context(recipient=recipient, context=context)
    config = get_notification_event_config(event_name)

    if config is None:
        raise ImproperlyConfigured(f"Notification event `{event_name}` is not registered.")

    notification = None

    if NotificationChannel.IN_APP in config.channels:
        notification = create_notification(
            user=recipient,
            notification_type=config.notification_type,
            title=_render_text(config.title, context),
            message=_render_text(config.message, context),
            related_object_type=context.get("related_object_type", ""),
            related_object_id=context.get("related_object_id"),
            data={
                "event_name": event_name,
                **context,
            },
        )

    if NotificationChannel.EMAIL in config.channels:
        if not config.email_subject or not config.email_body:
            raise ImproperlyConfigured(
                f"Notification event `{event_name}` has EMAIL channel, "
                "but email_subject or email_body is missing."
            )

        email_recipient = _get_email_recipient(recipient=recipient, context=context)

        send_email_notification(
            recipient=email_recipient,
            notification_type=config.notification_type,
            user=recipient,
            notification=notification,
            subject=_render_text(config.email_subject, context),
            body=_render_text(config.email_body, context),
            data={
                "event_name": event_name,
                **context,
            },
        )

    if NotificationChannel.PUSH in config.channels:

        delivery = NotificationDelivery.objects.create(
            notification=notification, # اگر IN_APP هم فعال بوده باشد، اینجا متصل می‌شود
            user=recipient,
            channel=NotificationChannel.PUSH,
            type=config.notification_type,
            recipient=str(recipient.pk),  # آیدی کاربر را به عنوان گیرنده ثبت می‌کنیم
            subject=_render_text(config.title, context),
            body=_render_text(config.message, context),
            status=NotificationDeliveryStatus.PENDING,
            data={"event_name": event_name, **context},
        )
        enqueue_notification_delivery(delivery=delivery)


def _build_context(*, recipient, context: dict[str, Any] | None) -> dict[str, Any]:
    payload = dict(context or {})

    payload.setdefault("user_id", recipient.pk)
    payload.setdefault("user_email", getattr(recipient, "email", ""))
    payload.setdefault("user_display_name", _get_user_display_name(recipient))

    return payload


def _get_user_display_name(user) -> str:
    if hasattr(user, "get_full_name"):
        full_name = user.get_full_name()
        if full_name:
            return full_name

    return getattr(user, "email", "") or getattr(user, "username", "") or str(user)


def _get_email_recipient(*, recipient, context: dict[str, Any]) -> str:
    email = context.get("email") or getattr(recipient, "email", "")

    if not email:
        raise ImproperlyConfigured(
            "Email notification requires recipient email or `email` in context."
        )
    try:
        validate_email(email)
    except ValidationError as err:
        raise ImproperlyConfigured(f"Invalid email address for notification: '{email}'") from err
    return email


def _render_text(template: str, context: dict[str, Any]) -> str:
    try:
        return template.format(**context)
    except KeyError as exc:
        missing_key = exc.args[0]
        raise ImproperlyConfigured(
            f"Missing notification template context key: `{missing_key}`."
        ) from exc
