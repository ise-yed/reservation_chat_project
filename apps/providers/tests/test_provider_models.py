import pytest

from apps.providers.tests.factories import ProviderProfileFactory

pytestmark = pytest.mark.django_db


def test_provider_profile_str_returns_user_name():
    """Test string representation returns user full name."""
    provider_profile = ProviderProfileFactory(
        user__first_name="Ali",
        user__last_name="Ahmadi",
    )
    assert str(provider_profile) == "Ali Ahmadi"


def test_provider_profile_str_returns_email_when_full_name_is_empty():
    """Test string representation fallbacks to email if full name is missing."""
    provider_profile = ProviderProfileFactory(
        user__first_name="",
        user__last_name="",
        user__email="provider@example.com",
    )
    assert str(provider_profile) == "provider@example.com"
