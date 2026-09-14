from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseNotificationChannel(ABC):
    """
    Base class for all notification channels.

    Every channel must implement the `send` method.
    Optionally can override `validate_recipient` and `get_backend_config`.
    """

    @abstractmethod
    def send(self, recipient: str, subject: str, body: str, **kwargs) -> None:
        """
        Send a notification through this channel.

        Args:
            recipient: Recipient identifier (email, phone, device token, etc.)
            subject: Notification subject
            body: Notification body/content
            **kwargs: Additional channel-specific parameters (e.g., html_message, from_email)
        """
        raise NotImplementedError

    def validate_recipient(self, recipient: str) -> bool:
        """Validate recipient format. Override in subclasses if needed."""
        return bool(recipient)

    def get_backend_config(self) -> Dict[str, Any]:
        """Return channel-specific configuration (e.g., API keys, timeouts)."""
        return {}
