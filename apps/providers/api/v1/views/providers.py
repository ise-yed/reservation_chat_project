from django.http import Http404
from rest_framework import generics, permissions, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from apps.organizations.models import Organization
from apps.organizations.permissions import can_manage_organization
from apps.organizations.selectors import get_organization_by_id
from apps.providers.api.v1.docs import (
    my_provider_profiles_schema,
    organization_providers_schema,
    provider_detail_schema,
    provider_list_create_schema,
)
from apps.providers.api.v1.serializers import (
    ProviderProfileCreateSerializer,
    ProviderProfileReadSerializer,
    ProviderProfileUpdateSerializer,
)
from apps.providers.models import ProviderProfile
from apps.providers.permissions import IsProviderProfileManagerOrReadOnly
from apps.providers.selectors import (
    get_active_providers,
    get_organization_providers,
    get_provider_by_id,
    get_user_provider_profiles,
)
from apps.providers.services import create_provider_profile, update_provider_profile


@provider_list_create_schema
class ProviderProfileListCreateView(generics.ListCreateAPIView):
    """
    View for listing and creating provider profiles.

    GET: Returns list of active provider profiles.
    POST: Creates a new provider profile (admin/org_admin only).
    """

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "organization__name",
        "branch__name",
        "title",
        "specialty",
    ]
    ordering_fields = ["created_at", "specialty"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Return all active provider profiles."""
        return get_active_providers()

    def get_serializer_class(self):
        """Use different serializers for read and write operations."""
        if self.request.method == "POST":
            return ProviderProfileCreateSerializer
        return ProviderProfileReadSerializer

    def create(self, request, *args, **kwargs):
        """Create a new provider profile."""
        serializer = ProviderProfileCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        provider_profile = create_provider_profile(
            actor=request.user,
            **serializer.validated_data,
        )

        output_serializer = ProviderProfileReadSerializer(provider_profile)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@provider_detail_schema
class ProviderProfileDetailView(generics.RetrieveUpdateAPIView):
    """
    View for retrieving and updating a single provider profile.

    GET: Returns provider details.
    PUT/PATCH: Updates provider profile (owner or org_admin only).
    """

    permission_classes = [
        permissions.IsAuthenticated,
        IsProviderProfileManagerOrReadOnly,
    ]

    def get_serializer_class(self):
        """Use different serializers for read and write operations."""
        if self.request.method in {"PUT", "PATCH"}:
            return ProviderProfileUpdateSerializer
        return ProviderProfileReadSerializer

    def get_object(self) -> ProviderProfile:
        """Retrieve and validate the provider profile with permission checks."""
        try:
            provider_profile = get_provider_by_id(
                provider_id=self.kwargs["pk"],
            )
        except ProviderProfile.DoesNotExist as exc:
            raise Http404 from exc

        can_manage_org = can_manage_organization(
            self.request.user,
            provider_profile.organization,
        )
        is_self_provider = provider_profile.user_id == self.request.user.id

        # Hide inactive providers from non-owners and non-self
        if not provider_profile.is_active and not (can_manage_org or is_self_provider):
            raise Http404

        # Hide providers of inactive organizations from non-owners
        if not provider_profile.organization.is_active and not can_manage_org:
            raise Http404

        self.check_object_permissions(self.request, provider_profile)
        return provider_profile

    def update(self, request, *args, **kwargs):
        """Update a provider profile with partial data support."""
        partial = kwargs.pop("partial", False)
        provider_profile = self.get_object()

        serializer = ProviderProfileUpdateSerializer(
            provider_profile,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)

        provider_profile = update_provider_profile(
            provider_profile=provider_profile,
            actor=request.user,
            **serializer.validated_data,
        )

        output_serializer = ProviderProfileReadSerializer(provider_profile)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


@my_provider_profiles_schema
class MyProviderProfileListView(generics.ListAPIView):
    """
    View for listing provider profiles where user is the provider.

    GET: Returns list of provider profiles for the current user.
    """

    serializer_class = ProviderProfileReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "organization__name",
        "branch__name",
        "title",
        "specialty",
    ]
    ordering_fields = ["created_at", "specialty"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Return only provider profiles for the current user."""
        return get_user_provider_profiles(user=self.request.user)


@organization_providers_schema
class OrganizationProviderListView(generics.ListAPIView):
    """
    View for listing provider profiles within an organization.

    GET: Returns providers in the organization (active only for non-owners).
    """

    serializer_class = ProviderProfileReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "branch__name",
        "title",
        "specialty",
    ]
    ordering_fields = ["created_at", "specialty"]
    ordering = ["-created_at"]

    def get_organization(self) -> Organization:
        """Retrieve and validate the organization."""
        try:
            organization = get_organization_by_id(
                organization_id=self.kwargs["organization_id"],
            )
        except Organization.DoesNotExist as exc:
            raise Http404 from exc

        # Hide inactive organizations from non-owners
        if not organization.is_active and not can_manage_organization(
            self.request.user,
            organization,
        ):
            raise Http404

        return organization

    def get_queryset(self):
        """Return providers filtered by organization and user permissions."""
        organization = self.get_organization()
        include_inactive = can_manage_organization(
            self.request.user,
            organization,
        )

        return get_organization_providers(
            organization=organization,
            include_inactive=include_inactive,
        )
