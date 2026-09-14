from django_filters import rest_framework as filters

from apps.offerings.models import Offering


class OfferingFilter(filters.FilterSet):
    """Filter for offerings."""

    category_id = filters.UUIDFilter(field_name="category__id")

    category_name = filters.CharFilter(field_name="category__name", lookup_expr="icontains")

    organization_id = filters.NumberFilter(field_name="organization__id")
    provider_id = filters.NumberFilter(field_name="provider__id")
    min_price = filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="price", lookup_expr="lte")

    class Meta:
        model = Offering
        fields = [
            "category_id",
            "category_name",
            "organization_id",
            "provider_id",
            "min_price",
            "max_price",
        ]
