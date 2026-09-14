import factory

from apps.offerings.models import Offering
from apps.providers.tests.factories import ProviderProfileFactory


class OfferingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Offering

    provider = factory.SubFactory(ProviderProfileFactory)

    @factory.lazy_attribute
    def organization(self):
        return self.provider.organization

    title = factory.Sequence(lambda n: f"Offering {n}")
    description = "Test offering description"
    duration_minutes = 30
    buffer_before_minutes = 0
    buffer_after_minutes = 0
    price = 100000
    requires_approval = False
    is_active = True
