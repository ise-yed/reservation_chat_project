from django.http import Http404
from rest_framework import generics, permissions, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from apps.availability.api.v1.docs import (
    holiday_detail_schema,
    holiday_list_create_schema,
    organization_holidays_schema,
)
from apps.availability.api.v1.serializers import (
    HolidayCreateSerializer,
    HolidayReadSerializer,
    HolidayUpdateSerializer,
)
from apps.availability.models import Holiday
from apps.availability.permissions import (
    IsHolidayManagerOrReadOnly,
    can_manage_holiday,
    can_manage_organization_holidays,
)
from apps.availability.selectors import (
    get_active_holidays,
    get_holiday_by_id,
    get_organization_holidays,
)
from apps.availability.services import create_holiday, update_holiday
from apps.organizations.models import Organization
from apps.organizations.selectors import get_organization_by_id


@holiday_detail_schema
class HolidayDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve and update holiday details."""

    permission_classes = [
        permissions.IsAuthenticated,
        IsHolidayManagerOrReadOnly,
    ]

    def get_serializer_class(self):
        if self.request.method in {"PUT", "PATCH"}:
            return HolidayUpdateSerializer
        return HolidayReadSerializer

    def get_object(self) -> Holiday:
        try:
            holiday = get_holiday_by_id(holiday_id=self.kwargs["pk"])
        except Holiday.DoesNotExist as exc:
            raise Http404 from exc

        can_manage = can_manage_holiday(self.request.user, holiday)

        if not holiday.is_active and not can_manage:
            raise Http404

        self.check_object_permissions(self.request, holiday)
        return holiday

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        holiday = self.get_object()

        serializer = HolidayUpdateSerializer(
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)

        holiday = update_holiday(
            holiday=holiday,
            actor=request.user,
            **serializer.validated_data,
        )

        output_serializer = HolidayReadSerializer(holiday)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


@holiday_list_create_schema
class HolidayListCreateView(generics.ListCreateAPIView):
    """List all active holidays and create new holiday."""

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["organization__name", "title"]
    ordering_fields = ["date", "created_at"]
    ordering = ["-date"]

    def get_queryset(self):
        return get_active_holidays()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return HolidayCreateSerializer
        return HolidayReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = HolidayCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        holiday = create_holiday(
            actor=request.user,
            **serializer.validated_data,
        )

        output_serializer = HolidayReadSerializer(holiday)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@organization_holidays_schema
class OrganizationHolidayListView(generics.ListAPIView):
    """List holidays for a specific organization."""

    serializer_class = HolidayReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["title"]
    ordering_fields = ["date", "created_at"]
    ordering = ["-date"]

    def get_organization(self) -> Organization:
        try:
            return get_organization_by_id(
                organization_id=self.kwargs["organization_id"],
            )
        except Organization.DoesNotExist as exc:
            raise Http404 from exc

    def get_queryset(self):
        organization = self.get_organization()
        include_inactive = can_manage_organization_holidays(
            self.request.user,
            organization,
        )

        return get_organization_holidays(
            organization=organization,
            include_inactive=include_inactive,
        )
