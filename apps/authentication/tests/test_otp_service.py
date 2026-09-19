from unittest.mock import patch

import pytest
from django.core.cache import cache

from apps.authentication.services.otp import OTPService
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestOTPService:
    def setup_method(self):
        cache.clear()

    def test_create_otp_success(self):
        user = UserFactory()
        code, error = OTPService.create_otp(user.id, user.email)
        assert code is not None
        assert error is None
        assert len(code) == 6

    def test_create_otp_cooldown_enforced(self):
        user = UserFactory()
        OTPService.create_otp(user.id, user.email)

        # Second immediate request should fail due to 60s cooldown
        code, error = OTPService.create_otp(user.id, user.email)
        assert code is None
        assert "wait 60 seconds" in error

    def test_create_otp_email_rate_limit(self):
        user = UserFactory()

        for _ in range(5):
            # Clear cooldown key to bypass 60s cooldown, but keep rate limit key intact
            cache.delete(OTPService._get_key(user.id, "password_reset"))
            code, error = OTPService.create_otp(user.id, user.email)
            assert code is not None

        # 6th request should fail due to Email Rate Limit (max 5)
        cache.delete(OTPService._get_key(user.id, "password_reset"))
        code, error = OTPService.create_otp(user.id, user.email)
        assert code is None
        assert "Too many requests" in error

    def test_verify_otp_success(self):
        user = UserFactory()
        code, _ = OTPService.create_otp(user.id, user.email)

        is_valid, msg = OTPService.verify_otp(user.id, code)
        assert is_valid is True
        assert msg is None

    def test_verify_otp_invalid_code_decrements_attempts(self):
        user = UserFactory()
        OTPService.create_otp(user.id, user.email)

        is_valid, msg = OTPService.verify_otp(user.id, "000000")
        assert is_valid is False
        assert "attempts remaining" in msg

    def test_verify_otp_max_attempts_lockout(self):
        user = UserFactory()
        OTPService.create_otp(user.id, user.email)

        OTPService.verify_otp(user.id, "000000")
        OTPService.verify_otp(user.id, "000000")
        is_valid, msg = OTPService.verify_otp(user.id, "000000")  # 3rd attempt

        assert is_valid is False
        assert "Too many failed attempts" in msg

        # 4th attempt should complain about expired/deleted OTP
        is_valid, msg = OTPService.verify_otp(user.id, "000000")
        assert is_valid is False
        assert "expired" in msg

    @patch("apps.authentication.services.otp.send_mail")
    def test_send_otp_email(self, mock_send_mail):
        user = UserFactory()
        mock_send_mail.return_value = 1

        success = OTPService.send_otp_email(user, "123456")
        assert success is True
        mock_send_mail.assert_called_once()
