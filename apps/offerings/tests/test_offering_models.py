import pytest

from apps.offerings.tests.factories import OfferingFactory

pytestmark = pytest.mark.django_db


def test_offering_str_returns_title_and_provider():
    offering = OfferingFactory(title="General Visit")

    assert "General Visit" in str(offering)
