"""
Factory classes for generating test data for Organization and Branch models.
"""

import factory

from apps.organizations.models import Branch, Organization
from apps.users.enums import UserRoles
from apps.users.tests.factories import UserFactory


class OrganizationFactory(factory.django.DjangoModelFactory):
    """Factory for creating Organization instances in tests."""

    class Meta:
        model = Organization

    owner = factory.SubFactory(UserFactory, role=UserRoles.PROVIDER)
    name = factory.Sequence(lambda n: f"Organization {n}")
    slug = factory.Sequence(lambda n: f"organization-{n}")
    description = "Test organization"
    phone_number = factory.Sequence(lambda n: f"02100000{n}")
    email = factory.Sequence(lambda n: f"org{n}@example.com")
    website = "https://example.com"
    timezone = "Asia/Tehran"
    is_active = True


class BranchFactory(factory.django.DjangoModelFactory):
    """Factory for creating Branch instances in tests."""

    class Meta:
        model = Branch

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Sequence(lambda n: f"Branch {n}")
    address = "Test address"
    phone_number = factory.Sequence(lambda n: f"02110000{n}")
    is_active = True
