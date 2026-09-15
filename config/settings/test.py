from .base import *

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

FRONTEND_PASSWORD_RESET_URL = "http://localhost:3000/reset-password"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
}

from rest_framework.throttling import SimpleRateThrottle

SimpleRateThrottle.allow_request = lambda self, request, view: True
