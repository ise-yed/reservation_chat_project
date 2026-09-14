from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email

from .base import BaseNotificationChannel


class EmailChannel(BaseNotificationChannel):
    """Send notifications through Django's email backend."""

    def send(self, recipient: str, subject: str, body: str, **kwargs) -> None:
        """
        Send an email.

        Additional kwargs:
            from_email (str): Sender email address (defaults to settings.DEFAULT_FROM_EMAIL)
            html_message (str): HTML version of the email
            fail_silently (bool): Override default fail_silently
        """
        from_email = kwargs.get("from_email", settings.DEFAULT_FROM_EMAIL)
        html_message = kwargs.get("html_message", None)
        fail_silently = kwargs.get("fail_silently", False)

        send_mail(
            subject=subject,
            message=body,
            from_email=from_email,
            recipient_list=[recipient],
            fail_silently=fail_silently,
            html_message=html_message,
        )

    def validate_recipient(self, recipient: str) -> bool:
        """Validate email format."""
        try:
            validate_email(recipient)
            return True
        except ValidationError:
            return False
