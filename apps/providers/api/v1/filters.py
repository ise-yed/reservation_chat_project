from django_filters import rest_framework as filters

from apps.providers.models import ProviderProfile


class ProviderProfileFilter(filters.FilterSet):
    """Filter set for ProviderProfile."""

    specialty_id = filters.UUIDFilter(field_name="specialties__id")

    class Meta:
        model = ProviderProfile
        fields = ["specialty_id"]
