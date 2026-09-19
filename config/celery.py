import logging
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
app = Celery("reservation")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "expire-unpaid-appointments": {
        "task": "apps.appointments.tasks.expire_unpaid_appointments_task",
        "schedule": 60.0,
    },
}



app.conf.update(
    EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend",
    DEFAULT_FROM_EMAIL="noreply@example.com",
    CELERY_SEND_TASK_ERROR_EMAILS=False,
)



logging.basicConfig(level=logging.DEBUG)
