import hashlib
import hmac
import logging
import secrets

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class OTPService:
    """Secure OTP service with Cooldown and Email-based Rate Limiting."""

    OTP_EXPIRE_SECONDS = 600
    MAX_ATTEMPTS = 3
    COOLDOWN_SECONDS = 60
    EMAIL_RATE_LIMIT_COUNT = 5
    EMAIL_RATE_LIMIT_TIMEOUT = 3600  # 1 Hour

    @staticmethod
    def _get_key(user_id, purpose):
        return f"otp:{purpose}:{user_id}"

    @staticmethod
    def _get_rate_limit_key(email, purpose):
        return f"otp_rate_limit:{purpose}:{email}"

    @staticmethod
    def generate_code():
        return f"{secrets.randbelow(900000) + 100000}"

    @staticmethod
    def _secure_compare(a, b):
        return hmac.compare_digest(a, b)

    @staticmethod
    def _hash_code(code):
        return hashlib.sha256(code.encode()).hexdigest()

    @staticmethod
    def create_otp(user_id, email, purpose="password_reset"):
        rate_key = OTPService._get_rate_limit_key(email, purpose)
        attempts = cache.get(rate_key, 0)
        if attempts >= OTPService.EMAIL_RATE_LIMIT_COUNT:
            return None, _("Too many requests for this email. Please try again later.")

        key = OTPService._get_key(user_id, purpose)
        existing_data = cache.get(key)
        if existing_data and "created_at" in existing_data:
            created_time = timezone.datetime.fromisoformat(existing_data["created_at"])
            if (timezone.now() - created_time).total_seconds() < OTPService.COOLDOWN_SECONDS:
                return None, _("Please wait 60 seconds before requesting a new code.")

        if attempts == 0:
            cache.set(rate_key, 1, timeout=OTPService.EMAIL_RATE_LIMIT_TIMEOUT)
        else:
            cache.incr(rate_key)

        cache.delete(key)
        code = OTPService.generate_code()

        data = {
            "code_hash": OTPService._hash_code(code),
            "attempts": 0,
            "created_at": timezone.now().isoformat(),
        }

        cache.set(key, data, timeout=OTPService.OTP_EXPIRE_SECONDS)
        return code, None

    @staticmethod
    def verify_otp(user_id, code, purpose="password_reset"):
        key = OTPService._get_key(user_id, purpose)
        data = cache.get(key)

        if not data:
            return False, _("OTP code has expired. Please request a new one.")

        if data["attempts"] >= OTPService.MAX_ATTEMPTS:
            cache.delete(key)
            return False, _("Too many failed attempts. Please request a new OTP.")

        stored_hash = data.get("code_hash")
        provided_hash = OTPService._hash_code(code)

        if not OTPService._secure_compare(provided_hash, stored_hash):
            data["attempts"] += 1
            remaining = OTPService.MAX_ATTEMPTS - data["attempts"]

            # پاک کردن فوری کلید در صورت اتمام دفعات مجاز
            if remaining <= 0:
                cache.delete(key)
                return False, _("Too many failed attempts. Please request a new OTP.")

            cache.set(key, data, timeout=OTPService.OTP_EXPIRE_SECONDS)
            return False, _("Invalid code. %(remaining)s attempts remaining.") % {"remaining": remaining}

        cache.delete(key)
        return True, None

    @staticmethod
    def send_otp_email(user, code, purpose_text="Password Reset"):
        try:
            sent_count = send_mail(
                subject=f"{purpose_text} OTP Code",
                message=f"Your {purpose_text} OTP code is: {code}\nIt will expire in 10 minutes.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
            if sent_count != 1:
                logger.error("Failed to send OTP email to user_id=%s", user.id)
                return False
            return True
        except Exception:
            logger.exception("Unexpected error sending OTP email to user_id=%s", user.id)
            return False
