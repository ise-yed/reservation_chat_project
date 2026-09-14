from typing import Any

from django.db import transaction

from apps.notifications.events.handlers import handle_notification_event


def publish_notification_event(
    *,
    event_name: str,
    recipient,
    context: dict[str, Any] | None = None,
    run_after_commit: bool = True,
) -> None:
    """
    Public notification event entrypoint for other apps.

    Other apps publish what happened; notifications decides how to deliver it.
    """
    payload = dict(context or {})

    def _publish() -> None:
        handle_notification_event(
            event_name=event_name,
            recipient=recipient,
            context=payload,
        )

    if run_after_commit:
        transaction.on_commit(_publish)
        return

    _publish()
