from django.http import Http404
from rest_framework import generics, permissions, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from apps.availability.api.v1.docs import (
    provider_time_offs_schema,
    time_off_detail_schema,
    time_off_list_create_schema,
)
from apps.availability.api.v1.serializers import (
    TimeOffCreateSerializer,
    TimeOffReadSerializer,
    TimeOffUpdateSerializer,
)
from apps.availability.models import TimeOff
from apps.availability.permissions import (
    IsTimeOffManagerOrReadOnly,
    can_manage_provider_availability,
)
from apps.availability.selectors import (
    get_active_time_offs,
    get_provider_time_offs,
    get_time_off_by_id,
)
from apps.availability.services import create_time_off, update_time_off
from apps.providers.models import ProviderProfile
from apps.providers.selectors import get_provider_by_id


@provider_time_offs_schema
class ProviderTimeOffListView(generics.ListAPIView):
    """List time offs for a specific provider."""

    serializer_class = TimeOffReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["reason"]
    ordering_fields = ["start_at", "end_at", "created_at"]
    ordering = ["-start_at"]

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

        return get_provider_time_offs(
            provider=provider,
            include_inactive=include_inactive,
        )


@time_off_list_create_schema
class TimeOffListCreateView(generics.ListCreateAPIView):
    """List all active time offs and create new time off."""

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "provider__user__email",
        "provider__user__first_name",
        "provider__user__last_name",
        "provider__organization__name",
        "reason",
    ]
    ordering_fields = ["start_at", "end_at", "created_at"]
    ordering = ["-start_at"]

    def get_queryset(self):
        return get_active_time_offs()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TimeOffCreateSerializer
        return TimeOffReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = TimeOffCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        time_off = create_time_off(
            actor=request.user,
            **serializer.validated_data,
        )

        output_serializer = TimeOffReadSerializer(time_off)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@time_off_detail_schema
class TimeOffDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve and update time off details."""

    permission_classes = [
        permissions.IsAuthenticated,
        IsTimeOffManagerOrReadOnly,
    ]

    def get_serializer_class(self):
        if self.request.method in {"PUT", "PATCH"}:
            return TimeOffUpdateSerializer
        return TimeOffReadSerializer

    def get_object(self) -> TimeOff:
        try:
            time_off = get_time_off_by_id(
                time_off_id=self.kwargs["pk"],
            )
        except TimeOff.DoesNotExist as exc:
            raise Http404 from exc

        can_manage = can_manage_provider_availability(
            self.request.user,
            time_off.provider,
        )

        if not time_off.is_active and not can_manage:
            raise Http404

        self.check_object_permissions(self.request, time_off)
        return time_off

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        time_off = self.get_object()

        serializer = TimeOffUpdateSerializer(
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)

        time_off = update_time_off(
            time_off=time_off,
            actor=request.user,
            **serializer.validated_data,
        )

        output_serializer = TimeOffReadSerializer(time_off)
        return Response(output_serializer.data, status=status.HTTP_200_OK)
