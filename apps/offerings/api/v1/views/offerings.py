from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from apps.offerings.api.v1.docs import (
    my_offerings_schema,
    offering_detail_schema,
    offering_list_create_schema,
    organization_offerings_schema,
    provider_offerings_schema,
)
from apps.offerings.api.v1.filters import OfferingFilter
from apps.offerings.api.v1.serializers import (
    OfferingCreateSerializer,
    OfferingReadSerializer,
    OfferingUpdateSerializer,
)
from apps.offerings.models import Offering
from apps.offerings.permissions import (
    IsOfferingManagerOrReadOnly,
    can_view_inactive_offering,
)
from apps.offerings.selectors import (
    get_active_offerings,
    get_offering_by_id,
    get_organization_offerings,
    get_provider_offerings,
    get_user_offerings,
)
from apps.offerings.services import create_offering, update_offering
from apps.organizations.models import Organization
from apps.organizations.permissions import can_manage_organization
from apps.organizations.selectors import get_organization_by_id
from apps.providers.models import ProviderProfile
from apps.providers.selectors import get_provider_by_id


@provider_offerings_schema
class ProviderOfferingListView(generics.ListAPIView):
    """List offerings for a specific provider."""

    serializer_class = OfferingReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "title",
        "description",
        "provider__specialties__name",
    ]
    ordering_fields = ["created_at", "title", "price", "duration_minutes"]
    ordering = ["-created_at"]

    def get_provider(self) -> ProviderProfile:
        try:
            provider = get_provider_by_id(
                provider_id=self.kwargs["provider_id"],
            )
        except ProviderProfile.DoesNotExist as exc:
            raise Http404 from exc

        can_manage_org = can_manage_organization(
            self.request.user,
            provider.organization,
        )
        is_self_provider = provider.user_id == self.request.user.id

        if not provider.is_active and not (can_manage_org or is_self_provider):
            raise Http404

        if not provider.organization.is_active and not can_manage_org:
            raise Http404

        return provider

    def get_queryset(self):
        provider = self.get_provider()

        include_inactive = (
            can_manage_organization(self.request.user, provider.organization)
            or provider.user_id == self.request.user.id
        )

        return get_provider_offerings(
            provider=provider,
            include_inactive=include_inactive,
        )


@organization_offerings_schema
class OrganizationOfferingListView(generics.ListAPIView):
    """List offerings for a specific organization."""

    serializer_class = OfferingReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "title",
        "description",
        "provider__user__email",
        "provider__user__first_name",
        "provider__user__last_name",
        "provider__specialties__name"
    ]
    ordering_fields = ["created_at", "title", "price", "duration_minutes"]
    ordering = ["-created_at"]

    def get_organization(self) -> Organization:
        try:
            organization = get_organization_by_id(
                organization_id=self.kwargs["organization_id"],
            )
        except Organization.DoesNotExist as exc:
            raise Http404 from exc

        if not organization.is_active and not can_manage_organization(
            self.request.user,
            organization,
        ):
            raise Http404

        return organization

    def get_queryset(self):
        organization = self.get_organization()
        include_inactive = can_manage_organization(
            self.request.user,
            organization,
        )

        return get_organization_offerings(
            organization=organization,
            include_inactive=include_inactive,
        )


@offering_list_create_schema
class OfferingListCreateView(generics.ListCreateAPIView):
    """List all active offerings and create new offering."""

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = [
        "title",
        "description",
        "organization__name",
        "provider__user__email",
        "provider__user__first_name",
        "provider__user__last_name",
        "provider__specialties__name",
    ]
    ordering_fields = ["created_at", "title", "price", "duration_minutes"]
    ordering = ["-created_at"]
    filterset_class = OfferingFilter

    def get_queryset(self):
        return get_active_offerings()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OfferingCreateSerializer
        return OfferingReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = OfferingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        offering = create_offering(
            actor=request.user,
            **serializer.validated_data,
        )

        output_serializer = OfferingReadSerializer(offering)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@my_offerings_schema
class MyOfferingListView(generics.ListAPIView):
    """List offerings for the authenticated user."""

    serializer_class = OfferingReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "title",
        "description",
        "organization__name",
        "provider__specialties__name",
    ]
    ordering_fields = ["created_at", "title", "price", "duration_minutes"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return get_user_offerings(user=self.request.user)


@offering_detail_schema
class OfferingDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve and update offering details."""

    permission_classes = [
        permissions.IsAuthenticated,
        IsOfferingManagerOrReadOnly,
    ]

    def get_serializer_class(self):
        if self.request.method in {"PUT", "PATCH"}:
            return OfferingUpdateSerializer
        return OfferingReadSerializer

    def get_object(self) -> Offering:
        try:
            offering = get_offering_by_id(
                offering_id=self.kwargs["pk"],
            )
        except Offering.DoesNotExist as exc:
            raise Http404 from exc

        if not offering.is_active and not can_view_inactive_offering(
            self.request.user,
            offering,
        ):
            raise Http404

        if not offering.organization.is_active and not can_view_inactive_offering(
            self.request.user,
            offering,
        ):
            raise Http404

        if not offering.provider.is_active and not can_view_inactive_offering(
            self.request.user,
            offering,
        ):
            raise Http404

        self.check_object_permissions(self.request, offering)
        return offering

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        offering = self.get_object()

        serializer = OfferingUpdateSerializer(
            offering,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)

        offering = update_offering(
            offering=offering,
            actor=request.user,
            **serializer.validated_data,
        )

        output_serializer = OfferingReadSerializer(offering)
        return Response(output_serializer.data, status=status.HTTP_200_OK)
