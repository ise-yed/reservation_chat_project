# events/__init__.py
from apps.notifications.events.dispatcher import publish_notification_event
from apps.notifications.events.event_types import NotificationEvent
from apps.notifications.events.handlers import handle_notification_event
from apps.notifications.events.registry import (
    NotificationEventConfig,
    get_notification_event_config,
)

__all__ = [
    "NotificationEvent",
    "publish_notification_event",
    "handle_notification_event",
    "NotificationEventConfig",
    "get_notification_event_config",
]
