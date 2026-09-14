import pytest

from apps.providers.tests.factories import ProviderProfileFactory

pytestmark = pytest.mark.django_db


def test_provider_profile_str_returns_user_name_and_specialty():
    provider_profile = ProviderProfileFactory(
        user__first_name="Ali",
        user__last_name="Ahmadi",
        specialty="Cardiology",
    )

    assert str(provider_profile) == "Ali Ahmadi - Cardiology"


def test_provider_profile_str_returns_email_when_full_name_is_empty():
    provider_profile = ProviderProfileFactory(
        user__first_name="",
        user__last_name="",
        user__email="provider@example.com",
        specialty="",
    )

    assert str(provider_profile) == "provider@example.com"
