from dataclasses import dataclass

from apps.notifications.enums import NotificationChannel, NotificationType
from apps.notifications.events.event_types import NotificationEvent


@dataclass(frozen=True)
class NotificationEventConfig:
    notification_type: str
    channels: tuple[str, ...]
    title: str
    message: str
    email_subject: str = ""
    email_body: str = ""


NOTIFICATION_EVENT_REGISTRY: dict[str, NotificationEventConfig] = {
    NotificationEvent.PASSWORD_CHANGED: NotificationEventConfig(
        notification_type=NotificationType.PASSWORD_CHANGED,
        channels=(
            NotificationChannel.IN_APP,
            NotificationChannel.EMAIL,
        ),
        title="Password changed",
        message="Your account password was changed successfully.",
        email_subject="Your password was changed",
        email_body=(
            "Hi {user_display_name},\n\n"
            "Your account password was changed successfully.\n\n"
            "If you did not make this change, please contact support immediately."
        ),
    ),
    NotificationEvent.PASSWORD_RESET_REQUESTED: NotificationEventConfig(
        notification_type=NotificationType.PASSWORD_RESET_REQUESTED,
        channels=(NotificationChannel.EMAIL,),
        title="Password reset requested",
        message="A password reset request was submitted for your account.",
        email_subject="Reset your password",
        email_body=(
            "Hi {user_display_name},\n\n"
            "We received a request to reset your password.\n\n"
            "Use this link to continue:\n"
            "{reset_link}\n\n"
            "If you did not request this, you can safely ignore this email."
        ),
    ),
    NotificationEvent.APPOINTMENT_CREATED: NotificationEventConfig(
        notification_type=NotificationType.APPOINTMENT_CREATED,
        channels=(
            NotificationChannel.IN_APP,
            NotificationChannel.EMAIL,
        ),
        title="Appointment scheduled",
        message=(
            "Appointment for {offering_title} between {customer_display_name} "
            "and {provider_display_name} is scheduled for {start_at_display}."
        ),
        email_subject="Appointment scheduled",
        email_body=(
            "Hi {user_display_name},\n\n"
            "An appointment has been scheduled.\n\n"
            "Service: {offering_title}\n"
            "Customer: {customer_display_name}\n"
            "Provider: {provider_display_name}\n"
            "Organization: {organization_name}\n"
            "Start: {start_at_display}\n"
            "End: {end_at_display}\n"
            "Status: {appointment_status}\n"
        ),
    ),
    NotificationEvent.APPOINTMENT_CONFIRMED: NotificationEventConfig(
        notification_type=NotificationType.APPOINTMENT_CONFIRMED,
        channels=(
            NotificationChannel.IN_APP,
            NotificationChannel.EMAIL,
        ),
        title="Appointment confirmed",
        message=("Appointment for {offering_title} on {start_at_display} has been confirmed."),
        email_subject="Appointment confirmed",
        email_body=(
            "Hi {user_display_name},\n\n"
            "The appointment has been confirmed.\n\n"
            "Service: {offering_title}\n"
            "Customer: {customer_display_name}\n"
            "Provider: {provider_display_name}\n"
            "Start: {start_at_display}\n"
            "End: {end_at_display}\n"
        ),
    ),
    NotificationEvent.APPOINTMENT_CANCELLED: NotificationEventConfig(
        notification_type=NotificationType.APPOINTMENT_CANCELLED,
        channels=(
            NotificationChannel.IN_APP,
            NotificationChannel.EMAIL,
        ),
        title="Appointment cancelled",
        message=(
            "Appointment for {offering_title} on {start_at_display} "
            "was cancelled by {cancelled_by_display_name}."
        ),
        email_subject="Appointment cancelled",
        email_body=(
            "Hi {user_display_name},\n\n"
            "The appointment was cancelled.\n\n"
            "Service: {offering_title}\n"
            "Customer: {customer_display_name}\n"
            "Provider: {provider_display_name}\n"
            "Start: {start_at_display}\n"
            "Cancelled by: {cancelled_by_display_name}\n"
            "Reason: {cancel_reason}\n"
        ),
    ),
    NotificationEvent.APPOINTMENT_COMPLETED: NotificationEventConfig(
        notification_type=NotificationType.APPOINTMENT_COMPLETED,
        channels=(NotificationChannel.IN_APP,),
        title="Appointment completed",
        message=("Appointment for {offering_title} on {start_at_display} has been completed."),
    ),
    NotificationEvent.APPOINTMENT_NO_SHOW: NotificationEventConfig(
        notification_type=NotificationType.APPOINTMENT_NO_SHOW,
        channels=(NotificationChannel.IN_APP,),
        title="Appointment marked as no-show",
        message=("Appointment for {offering_title} on {start_at_display} was marked as no-show."),
    ),
    NotificationEvent.APPOINTMENT_REMINDER: NotificationEventConfig(
        notification_type=NotificationType.APPOINTMENT_REMINDER,
        channels=(NotificationChannel.EMAIL,),
        title="Appointment reminder",
        message="Reminder: appointment for {offering_title} starts at {start_at_display}.",
        email_subject="Appointment reminder",
        email_body=(
            "Hi {user_display_name},\n\n"
            "This is a reminder for your upcoming appointment.\n\n"
            "Service: {offering_title}\n"
            "Customer: {customer_display_name}\n"
            "Provider: {provider_display_name}\n"
            "Organization: {organization_name}\n"
            "Start: {start_at_display}\n"
            "End: {end_at_display}\n\n"
            "Thank you."
        ),
    ),
    NotificationEvent.PAYMENT_SUCCESS: NotificationEventConfig(
        notification_type=NotificationType.PAYMENT_SUCCESS,
        channels=(
            NotificationChannel.IN_APP,
            NotificationChannel.EMAIL,
        ),
        title="Payment successful",
        message="Payment for {offering_title} was completed successfully.",
        email_subject="Payment successful",
        email_body=(
            "Hi {user_display_name},\n\n"
            "Your payment was completed successfully.\n\n"
            "Service: {offering_title}\n"
            "Amount: {payment_amount} {payment_currency}\n"
            "Organization: {organization_name}\n"
            "Appointment time: {appointment_start_at_display}\n"
            "Reference: {gateway_reference}\n"
        ),
    ),
    NotificationEvent.PAYMENT_FAILED: NotificationEventConfig(
        notification_type=NotificationType.PAYMENT_FAILED,
        channels=(
            NotificationChannel.IN_APP,
            NotificationChannel.EMAIL,
        ),
        title="Payment failed",
        message="Payment for {offering_title} was failed.",
        email_subject="Payment failed",
        email_body=(
            "Hi {user_display_name},\n\n"
            "Your payment was not completed.\n\n"
            "Service: {offering_title}\n"
            "Amount: {payment_amount} {payment_currency}\n"
            "Organization: {organization_name}\n"
            "Appointment time: {appointment_start_at_display}\n"
        ),
    ),
    NotificationEvent.REFUND_SUCCESS: NotificationEventConfig(
        notification_type=NotificationType.REFUND_SUCCESS,
        channels=(
            NotificationChannel.IN_APP,
            NotificationChannel.EMAIL,
        ),
        title="Refund successful",
        message="Refund for {offering_title} was completed successfully.",
        email_subject="Refund successful",
        email_body=(
            "Hi {user_display_name},\n\n"
            "Your refund was completed successfully.\n\n"
            "Service: {offering_title}\n"
            "Amount: {payment_amount} {payment_currency}\n"
            "Organization: {organization_name}\n"
            "Appointment time: {appointment_start_at_display}\n"
        ),
    ),
}


def get_notification_event_config(event_name: str) -> NotificationEventConfig | None:
    return NOTIFICATION_EVENT_REGISTRY.get(event_name)
