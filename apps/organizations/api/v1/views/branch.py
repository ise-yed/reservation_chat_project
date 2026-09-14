"""
API views for Branch endpoints.

Handles listing, creating, retrieving, and updating branches.
"""

from django.http import Http404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from apps.organizations.api.v1.docs import (
    branch_detail_schema,
    branch_list_create_schema,
)
from apps.organizations.api.v1.serializers import (
    BranchCreateSerializer,
    BranchReadSerializer,
    BranchUpdateSerializer,
)
from apps.organizations.models import Branch, Organization
from apps.organizations.permissions import (
    IsBranchOrganizationOwnerOrReadOnly,
    can_manage_organization,
)
from apps.organizations.selectors import (
    get_branch_by_id,
    get_organization_branches,
    get_organization_by_id,
)
from apps.organizations.services import (
    create_branch,
    update_branch,
)


@branch_list_create_schema
class BranchListCreateView(generics.ListCreateAPIView):
    """
    View for listing and creating branches.

    GET: Returns list of branches (active only for non-owners).
    POST: Creates a new branch (owner only).
    """

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "phone_number", "address"]
    ordering_fields = ["created_at", "name"]
    ordering = ["name"]

    def get_organization(self) -> Organization:
        """Retrieve and validate the parent organization."""
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
        """Return branches filtered by organization and user permissions."""
        organization = self.get_organization()
        include_inactive = can_manage_organization(self.request.user, organization)

        return get_organization_branches(
            organization=organization,
            include_inactive=include_inactive,
        )

    def get_serializer_class(self):
        """Use different serializers for read and write operations."""
        if self.request.method == "POST":
            return BranchCreateSerializer
        return BranchReadSerializer

    def create(self, request, *args, **kwargs):
        """Create a new branch under the organization."""
        organization = self.get_organization()

        if not can_manage_organization(request.user, organization):
            raise PermissionDenied("You are not allowed to manage this organization.")

        serializer = BranchCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        branch = create_branch(
            organization=organization,
            actor=request.user,
            **serializer.validated_data,
        )

        output_serializer = BranchReadSerializer(branch)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@branch_detail_schema
class BranchDetailView(generics.RetrieveUpdateAPIView):
    """
    View for retrieving and updating a single branch.

    GET: Returns branch details (any authenticated user).
    PUT/PATCH: Updates branch (owner only).
    """

    permission_classes = [
        permissions.IsAuthenticated,
        IsBranchOrganizationOwnerOrReadOnly,
    ]

    def get_serializer_class(self):
        """Use different serializers for read and write operations."""
        if self.request.method in {"PUT", "PATCH"}:
            return BranchUpdateSerializer
        return BranchReadSerializer

    def get_object(self) -> Branch:
        """Retrieve and validate the branch with permission checks."""
        try:
            branch = get_branch_by_id(branch_id=self.kwargs["pk"])
        except Branch.DoesNotExist as exc:
            raise Http404 from exc

        # Hide inactive branches from non-owners
        if not branch.is_active and not can_manage_organization(
            self.request.user,
            branch.organization,
        ):
            raise Http404

        # Hide branches of inactive organizations from non-owners
        if not branch.organization.is_active and not can_manage_organization(
            self.request.user,
            branch.organization,
        ):
            raise Http404

        self.check_object_permissions(self.request, branch)
        return branch

    def update(self, request, *args, **kwargs):
        """Update a branch with partial data support."""
        partial = kwargs.pop("partial", False)
        branch = self.get_object()

        serializer = BranchUpdateSerializer(
            branch,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)

        branch = update_branch(
            branch=branch,
            actor=request.user,
            **serializer.validated_data,
        )

        output_serializer = BranchReadSerializer(branch)
        return Response(output_serializer.data, status=status.HTTP_200_OK)
