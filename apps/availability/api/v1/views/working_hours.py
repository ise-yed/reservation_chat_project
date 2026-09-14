from django.http import Http404
from rest_framework import generics, permissions, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from apps.availability.api.v1.docs import (
    provider_working_hours_schema,
    working_hour_detail_schema,
    working_hour_list_create_schema,
)
from apps.availability.api.v1.serializers import (
    WorkingHourCreateSerializer,
    WorkingHourReadSerializer,
    WorkingHourUpdateSerializer,
)
from apps.availability.models import WorkingHour
from apps.availability.permissions import (
    IsWorkingHourManagerOrReadOnly,
    can_manage_provider_availability,
)
from apps.availability.selectors import (
    get_active_working_hours,
    get_provider_working_hours,
    get_working_hour_by_id,
)
from apps.availability.services import create_working_hour, update_working_hour
from apps.providers.models import ProviderProfile
from apps.providers.selectors import get_provider_by_id


@provider_working_hours_schema
class ProviderWorkingHourListView(generics.ListAPIView):
    """List working hours for a specific provider."""

    serializer_class = WorkingHourReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [OrderingFilter]
    ordering_fields = ["weekday", "start_time"]
    ordering = ["weekday", "start_time"]

    def get_provider(self) -> ProviderProfile:
        try:
            return get_provider_by_id(provider_id=self.kwargs["provider_id"])
        except ProviderProfile.DoesNotExist as exc:
            raise Http404 from exc

    def get_queryset(self):
        provider = self.get_provider()
        include_inactive = can_manage_provider_availability(
            self.request.user,
            provider,
        )

        return get_provider_working_hours(
            provider=provider,
            include_inactive=include_inactive,
        )


@working_hour_list_create_schema
class WorkingHourListCreateView(generics.ListCreateAPIView):
    """List all active working hours and create new working hour."""

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "provider__user__email",
        "provider__user__first_name",
        "provider__user__last_name",
        "provider__organization__name",
        "provider__specialty",
    ]
    ordering_fields = ["weekday", "start_time", "created_at"]
    ordering = ["weekday", "start_time"]

    def get_queryset(self):
        return get_active_working_hours()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return WorkingHourCreateSerializer
        return WorkingHourReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = WorkingHourCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        working_hour = create_working_hour(
            actor=request.user,
            **serializer.validated_data,
        )

        output_serializer = WorkingHourReadSerializer(working_hour)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@working_hour_detail_schema
class WorkingHourDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve and update working hour details."""

    permission_classes = [
        permissions.IsAuthenticated,
        IsWorkingHourManagerOrReadOnly,
    ]

    def get_serializer_class(self):
        if self.request.method in {"PUT", "PATCH"}:
            return WorkingHourUpdateSerializer
        return WorkingHourReadSerializer

    def get_object(self) -> WorkingHour:
        try:
            working_hour = get_working_hour_by_id(
                working_hour_id=self.kwargs["pk"],
            )
        except WorkingHour.DoesNotExist as exc:
            raise Http404 from exc

        can_manage = can_manage_provider_availability(
            self.request.user,
            working_hour.provider,
        )

        if not working_hour.is_active and not can_manage:
            raise Http404

        self.check_object_permissions(self.request, working_hour)
        return working_hour

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        working_hour = self.get_object()

        serializer = WorkingHourUpdateSerializer(
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)

        working_hour = update_working_hour(
            working_hour=working_hour,
            actor=request.user,
            **serializer.validated_data,
        )

        output_serializer = WorkingHourReadSerializer(working_hour)
        return Response(output_serializer.data, status=status.HTTP_200_OK)
