import pytest
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.offerings.services import create_offering, update_offering
from apps.offerings.tests.factories import OfferingFactory
from apps.organizations.tests.factories import OrganizationFactory
from apps.providers.tests.factories import ProviderProfileFactory
from apps.users.enums import UserRoles
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_organization_owner_can_create_offering():
    owner = UserFactory(role=UserRoles.PROVIDER)
    organization = OrganizationFactory(owner=owner)
    provider = ProviderProfileFactory(organization=organization)

    offering = create_offering(
        actor=owner,
        organization_id=organization.id,
        provider_id=provider.id,
        title="General Visit",
        duration_minutes=30,
        price=100000,
    )

    assert offering.organization == organization
    assert offering.provider == provider
    assert offering.title == "General Visit"


def test_non_owner_cannot_create_offering():
    owner = UserFactory(role=UserRoles.PROVIDER)
    other_user = UserFactory(role=UserRoles.PROVIDER)
    organization = OrganizationFactory(owner=owner)
    provider = ProviderProfileFactory(organization=organization)

    with pytest.raises(PermissionDenied):
        create_offering(
            actor=other_user,
            organization_id=organization.id,
            provider_id=provider.id,
            title="Invalid Offering",
        )


def test_cannot_create_offering_for_provider_from_another_organization():
    owner = UserFactory(role=UserRoles.PROVIDER)
    organization = OrganizationFactory(owner=owner)
    other_organization = OrganizationFactory()
    provider = ProviderProfileFactory(organization=other_organization)

    with pytest.raises(ValidationError):
        create_offering(
            actor=owner,
            organization_id=organization.id,
            provider_id=provider.id,
            title="Invalid Offering",
        )


def test_cannot_create_duplicate_offering_title_for_same_provider():
    owner = UserFactory(role=UserRoles.PROVIDER)
    organization = OrganizationFactory(owner=owner)
    provider = ProviderProfileFactory(organization=organization)

    create_offering(
        actor=owner,
        organization_id=organization.id,
        provider_id=provider.id,
        title="General Visit",
    )

    with pytest.raises(ValidationError):
        create_offering(
            actor=owner,
            organization_id=organization.id,
            provider_id=provider.id,
            title="general visit",
        )


def test_cannot_create_offering_with_negative_price():
    owner = UserFactory(role=UserRoles.PROVIDER)
    organization = OrganizationFactory(owner=owner)
    provider = ProviderProfileFactory(organization=organization)

    with pytest.raises(ValidationError):
        create_offering(
            actor=owner,
            organization_id=organization.id,
            provider_id=provider.id,
            title="General Visit",
            price=-1,
        )


def test_owner_can_update_offering():
    owner = UserFactory(role=UserRoles.PROVIDER)
    organization = OrganizationFactory(owner=owner)
    provider = ProviderProfileFactory(organization=organization)
    offering = OfferingFactory(
        organization=organization,
        provider=provider,
        title="Old Offering",
    )

    updated = update_offering(
        offering=offering,
        actor=owner,
        title="New Offering",
        price=200000,
    )

    assert updated.title == "New Offering"
    assert updated.price == 200000


def test_non_owner_cannot_update_offering():
    owner = UserFactory(role=UserRoles.PROVIDER)
    other_user = UserFactory(role=UserRoles.PROVIDER)
    organization = OrganizationFactory(owner=owner)
    provider = ProviderProfileFactory(organization=organization)
    offering = OfferingFactory(
        organization=organization,
        provider=provider,
    )

    with pytest.raises(PermissionDenied):
        update_offering(
            offering=offering,
            actor=other_user,
            title="Invalid",
        )
