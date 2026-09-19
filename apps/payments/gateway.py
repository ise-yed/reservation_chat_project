import secrets

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class BaseGateway:
    def start(self, *, payment, callback_url: str) -> tuple[str, str]:
        """Return (authority, pay_url)."""
        raise NotImplementedError

    def verify(self, *, payment, params: dict) -> str | None:
        """Return the gateway reference if the payment succeeded, otherwise None."""
        raise NotImplementedError


class MockGateway(BaseGateway):
    """
    Development / test gateway. pay_url points straight back to our callback.
    Change `status=OK` to `status=NOK` in that URL to simulate a failed payment.
    Never use in production.
    """

    def start(self, *, payment, callback_url):
        authority = f"mock-{secrets.token_hex(12)}"
        return authority, f"{callback_url}?authority={authority}&status=OK"

    def verify(self, *, payment, params):
        authority = params.get("authority")
        if params.get("status") == "OK" and authority and authority == payment.gateway_reference:
            return authority
        return None


def get_gateway() -> BaseGateway:
    name = getattr(settings, "PAYMENT_GATEWAY", "mock")
    if name == "mock":
        return MockGateway()
    # Add real gateways here (e.g. a ZarinPal class implementing start/verify).
    raise ImproperlyConfigured(f"Unknown PAYMENT_GATEWAY: {name!r}")
