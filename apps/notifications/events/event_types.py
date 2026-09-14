from django.utils.translation import gettext_lazy as _


class NotificationEvent:
    PASSWORD_CHANGED = "authentication.password_changed"
    PASSWORD_RESET_REQUESTED = "authentication.password_reset_requested"

    APPOINTMENT_CREATED = "appointments.appointment_created"
    APPOINTMENT_CONFIRMED = "appointments.appointment_confirmed"
    APPOINTMENT_CANCELLED = "appointments.appointment_cancelled"
    APPOINTMENT_COMPLETED = "appointments.appointment_completed"
    APPOINTMENT_NO_SHOW = "appointments.appointment_no_show"
    APPOINTMENT_REMINDER = "appointments.appointment_reminder"

    PAYMENT_SUCCESS = "payments.payment_success"
    PAYMENT_FAILED = "payments.payment_failed"
    REFUND_SUCCESS = "payments.refund_success"

    @classmethod
    def choices(cls):
        return (
            (cls.PASSWORD_CHANGED, _("Password changed")),
            (cls.PASSWORD_RESET_REQUESTED, _("Password reset requested")),
            (cls.APPOINTMENT_CREATED, _("Appointment created")),
            (cls.APPOINTMENT_CONFIRMED, _("Appointment confirmed")),
            (cls.APPOINTMENT_CANCELLED, _("Appointment cancelled")),
            (cls.APPOINTMENT_COMPLETED, _("Appointment completed")),
            (cls.APPOINTMENT_NO_SHOW, _("Appointment no show")),
            (cls.APPOINTMENT_REMINDER, _("Appointment reminder")),
            (cls.PAYMENT_SUCCESS, "Payment success"),
            (cls.PAYMENT_FAILED, "Payment failed"),
            (cls.REFUND_SUCCESS, "Refund success"),
        )
