import pytest

from apps.notifications.enums import NotificationType
from apps.notifications.events.event_types import NotificationEvent
from apps.notifications.events.registry import get_notification_event_config


@pytest.mark.parametrize(
    "event_name, notification_type",
    [
        (NotificationEvent.APPOINTMENT_CREATED, NotificationType.APPOINTMENT_CREATED),
        (NotificationEvent.APPOINTMENT_CONFIRMED, NotificationType.APPOINTMENT_CONFIRMED),
        (NotificationEvent.APPOINTMENT_CANCELLED, NotificationType.APPOINTMENT_CANCELLED),
        (NotificationEvent.APPOINTMENT_COMPLETED, NotificationType.APPOINTMENT_COMPLETED),
        (NotificationEvent.APPOINTMENT_NO_SHOW, NotificationType.APPOINTMENT_NO_SHOW),
        (NotificationEvent.APPOINTMENT_REMINDER, NotificationType.APPOINTMENT_REMINDER),
    ],
)
def test_appointment_notification_events_are_registered(event_name, notification_type):
    config = get_notification_event_config(event_name)

    assert config is not None
    assert config.notification_type == notification_type
