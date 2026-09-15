# conftest.py
import pytest


@pytest.fixture(autouse=True)
def _disable_throttling(monkeypatch):
    """
    همه throttleهای DRF رو در تست‌ها غیرفعال می‌کنه.
    چه throttle از settings بیاد، چه روی خود view تعریف شده باشه.
    """
    from rest_framework.throttling import BaseThrottle

    def _allow_all(self, request, view):
        return True

    monkeypatch.setattr(BaseThrottle, "allow_request", _allow_all)
