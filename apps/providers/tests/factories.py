import factory

from apps.organizations.tests.factories import BranchFactory, OrganizationFactory
from apps.providers.models import ProviderProfile
from apps.users.enums import UserRoles
from apps.users.tests.factories import UserFactory


class ProviderProfileFactory(factory.django.DjangoModelFactory):
    """Factory for creating ProviderProfile instances in tests."""

    class Meta:
        model = ProviderProfile

    user = factory.SubFactory(UserFactory, role=UserRoles.PROVIDER)
    organization = factory.SubFactory(OrganizationFactory)
    branch = factory.SubFactory(BranchFactory)
    title = "Dr."
    bio = "Test provider bio"
    default_slot_duration_minutes = 30
    is_active = True

    @factory.post_generation
    def specialties(self, create, extracted, **kwargs):
        """Handle ManyToMany relationship for specialties after instance creation."""
        if not create:
            return
        if extracted:
            for specialty in extracted:
                self.specialties.add(specialty)
