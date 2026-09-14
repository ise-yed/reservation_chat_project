from datetime import date, time, timedelta

import factory
from django.utils import timezone

from apps.availability.models import Holiday, TimeOff, Weekday, WorkingHour
from apps.providers.tests.factories import ProviderProfileFactory


class WorkingHourFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WorkingHour

    provider = factory.SubFactory(ProviderProfileFactory)
    weekday = Weekday.MONDAY
    start_time = time(9, 0)
    end_time = time(17, 0)
    is_active = True


class TimeOffFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TimeOff

    provider = factory.SubFactory(ProviderProfileFactory)
    start_at = factory.LazyFunction(lambda: timezone.now() + timedelta(days=1, hours=1))
    end_at = factory.LazyFunction(lambda: timezone.now() + timedelta(days=1, hours=2))
    reason = "Test time off"
    is_active = True


class HolidayFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Holiday

    organization = factory.LazyAttribute(lambda obj: ProviderProfileFactory().organization)
    date = factory.LazyFunction(lambda: date.today() + timedelta(days=1))
    title = "Test holiday"
    is_active = True
