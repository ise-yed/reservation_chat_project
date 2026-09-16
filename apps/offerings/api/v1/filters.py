from django_filters import rest_framework as filters

from apps.offerings.enums import VisitMode
from apps.offerings.models import Offering


class OfferingFilter(filters.FilterSet):
    """Filter for offerings."""

    specialty_id = filters.UUIDFilter(field_name="specialty__id")
    specialty_name = filters.CharFilter(field_name="specialty__name", lookup_expr="icontains")

    organization_id = filters.UUIDFilter(field_name="organization__id")
    provider_id = filters.UUIDFilter(field_name="provider__id")

    visit_mode = filters.ChoiceFilter(choices=VisitMode.choices)

    min_price = filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="price", lookup_expr="lte")

    class Meta:
        model = Offering
        fields = [
            "specialty_id",
            "specialty_name",
            "organization_id",
            "provider_id",
            "visit_mode",
            "min_price",
            "max_price",
        ]
