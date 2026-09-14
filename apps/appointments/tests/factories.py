import factory

from apps.appointments.enums import AppointmentStatus
from apps.appointments.models import Appointment
from apps.offerings.tests.factories import OfferingFactory
from apps.users.tests.factories import UserFactory


class AppointmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Appointment

    customer = factory.SubFactory(UserFactory)
    offering = factory.SubFactory(OfferingFactory)

    @factory.lazy_attribute
    def provider(self):
        return self.offering.provider

    @factory.lazy_attribute
    def organization(self):
        return self.provider.organization

    @factory.lazy_attribute
    def branch(self):
        return self.provider.branch

    start_at = factory.LazyFunction(lambda: None)
    end_at = factory.LazyFunction(lambda: None)
    blocked_start_at = factory.LazyFunction(lambda: None)
    blocked_end_at = factory.LazyFunction(lambda: None)

    status = AppointmentStatus.CONFIRMED
    price = factory.LazyAttribute(lambda obj: obj.offering.price)
    notes = "Test appointment"
    created_by = factory.SelfAttribute("customer")
