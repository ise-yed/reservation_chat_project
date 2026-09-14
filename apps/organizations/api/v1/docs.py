from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)

from apps.organizations.api.v1.serializers import (
    BranchCreateSerializer,
    BranchReadSerializer,
    BranchUpdateSerializer,
    OrganizationCreateSerializer,
    OrganizationReadSerializer,
    OrganizationUpdateSerializer,
)

organization_list_create_schema = extend_schema_view(
    get=extend_schema(
        summary="List active organizations",
        description="Returns active organizations available in the reservation system.",
        responses={200: OrganizationReadSerializer(many=True)},
        tags=["Organizations"],
    ),
    post=extend_schema(
        summary="Create organization",
        description=(
            "Creates a new organization. Provider, organization admin,"
            " or super admin can create it."
        ),
        request=OrganizationCreateSerializer,
        responses={
            201: OrganizationReadSerializer,
            400: OpenApiResponse(description="Invalid organization data."),
            403: OpenApiResponse(description="Permission denied."),
        },
        tags=["Organizations"],
    ),
)


my_organizations_schema = extend_schema(
    summary="List my organizations",
    description="Returns organizations owned by the authenticated user.",
    responses={200: OrganizationReadSerializer(many=True)},
    tags=["Organizations"],
)


organization_detail_schema = extend_schema_view(
    get=extend_schema(
        summary="Retrieve organization",
        responses={
            200: OrganizationReadSerializer,
            404: OpenApiResponse(description="Organization not found."),
        },
        tags=["Organizations"],
    ),
    patch=extend_schema(
        summary="Update organization",
        request=OrganizationUpdateSerializer,
        responses={
            200: OrganizationReadSerializer,
            400: OpenApiResponse(description="Invalid organization data."),
            403: OpenApiResponse(description="Permission denied."),
            404: OpenApiResponse(description="Organization not found."),
        },
        tags=["Organizations"],
    ),
    put=extend_schema(
        summary="Update organization",
        request=OrganizationUpdateSerializer,
        responses={
            200: OrganizationReadSerializer,
            400: OpenApiResponse(description="Invalid organization data."),
            403: OpenApiResponse(description="Permission denied."),
            404: OpenApiResponse(description="Organization not found."),
        },
        tags=["Organizations"],
    ),
)


branch_list_create_schema = extend_schema_view(
    get=extend_schema(
        summary="List organization branches",
        parameters=[
            OpenApiParameter(
                name="organization_id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                required=True,
            )
        ],
        responses={200: BranchReadSerializer(many=True)},
        tags=["Organization Branches"],
    ),
    post=extend_schema(
        summary="Create organization branch",
        request=BranchCreateSerializer,
        responses={
            201: BranchReadSerializer,
            400: OpenApiResponse(description="Invalid branch data."),
            403: OpenApiResponse(description="Permission denied."),
            404: OpenApiResponse(description="Organization not found."),
        },
        tags=["Organization Branches"],
    ),
)


branch_detail_schema = extend_schema_view(
    get=extend_schema(
        summary="Retrieve branch",
        responses={
            200: BranchReadSerializer,
            404: OpenApiResponse(description="Branch not found."),
        },
        tags=["Organization Branches"],
    ),
    patch=extend_schema(
        summary="Update branch",
        request=BranchUpdateSerializer,
        responses={
            200: BranchReadSerializer,
            400: OpenApiResponse(description="Invalid branch data."),
            403: OpenApiResponse(description="Permission denied."),
            404: OpenApiResponse(description="Branch not found."),
        },
        tags=["Organization Branches"],
    ),
    put=extend_schema(
        summary="Update branch",
        request=BranchUpdateSerializer,
        responses={
            200: BranchReadSerializer,
            400: OpenApiResponse(description="Invalid branch data."),
            403: OpenApiResponse(description="Permission denied."),
            404: OpenApiResponse(description="Branch not found."),
        },
        tags=["Organization Branches"],
    ),
)
