"""
API views for Organization endpoints.

Handles listing, creating, retrieving, and updating organizations.
"""

from django.http import Http404
from rest_framework import generics, permissions, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from apps.organizations.api.v1.docs import (
    my_organizations_schema,
    organization_detail_schema,
    organization_list_create_schema,
)
from apps.organizations.api.v1.serializers import (
    OrganizationCreateSerializer,
    OrganizationReadSerializer,
    OrganizationUpdateSerializer,
)
from apps.organizations.models import Organization
from apps.organizations.permissions import (
    CanCreateOrganizationOrReadOnly,
    IsOrganizationOwnerOrReadOnly,
    can_manage_organization,
)
from apps.organizations.selectors import (
    get_active_organizations,
    get_organization_by_id,
    get_user_owned_organizations,
)
from apps.organizations.services import (
    create_organization,
    update_organization,
)


@organization_list_create_schema
class OrganizationListCreateView(generics.ListCreateAPIView):
    """
    View for listing and creating organizations.

    GET: Returns list of active organizations (authenticated users only).
    POST: Creates a new organization (provider/org_admin/super_admin only).
    """

    permission_classes = [
        permissions.IsAuthenticated,
        CanCreateOrganizationOrReadOnly,
    ]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "slug", "phone_number", "email"]
    ordering_fields = ["created_at", "name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Return only active organizations with annotated branch counts."""
        return get_active_organizations()

    def get_serializer_class(self):
        """Use different serializers for read and write operations."""
        if self.request.method == "POST":
            return OrganizationCreateSerializer
        return OrganizationReadSerializer

    def create(self, request, *args, **kwargs):
        """Create a new organization for the authenticated user."""
        serializer = OrganizationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        organization = create_organization(
            owner=request.user,
            **serializer.validated_data,
        )

        output_serializer = OrganizationReadSerializer(organization)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@my_organizations_schema
class MyOrganizationListView(generics.ListAPIView):
    """
    View for listing organizations owned by the authenticated user.

    GET: Returns list of user's own organizations.
    """

    serializer_class = OrganizationReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "slug", "phone_number", "email"]
    ordering_fields = ["created_at", "name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Return only organizations owned by the current user."""
        return get_user_owned_organizations(user=self.request.user)


@organization_detail_schema
class OrganizationDetailView(generics.RetrieveUpdateAPIView):
    """
    View for retrieving and updating a single organization.

    GET: Returns organization details (any authenticated user).
    PUT/PATCH: Updates organization (owner only).
    """

    permission_classes = [
        permissions.IsAuthenticated,
        IsOrganizationOwnerOrReadOnly,
    ]

    def get_serializer_class(self):
        """Use different serializers for read and write operations."""
        if self.request.method in {"PUT", "PATCH"}:
            return OrganizationUpdateSerializer
        return OrganizationReadSerializer

    def get_object(self) -> Organization:
        """Retrieve and validate the organization with permission checks."""
        try:
            organization = get_organization_by_id(
                organization_id=self.kwargs["pk"],
            )
        except Organization.DoesNotExist as exc:
            raise Http404 from exc

        if not organization.is_active and not can_manage_organization(
            self.request.user,
            organization,
        ):
            raise Http404

        self.check_object_permissions(self.request, organization)
        return organization

    def update(self, request, *args, **kwargs):
        """Update an organization with partial data support."""
        partial = kwargs.pop("partial", False)
        organization = self.get_object()

        serializer = OrganizationUpdateSerializer(
            organization,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)

        organization = update_organization(
            organization=organization,
            actor=request.user,
            **serializer.validated_data,
        )

        output_serializer = OrganizationReadSerializer(organization)
        return Response(output_serializer.data, status=status.HTTP_200_OK)
