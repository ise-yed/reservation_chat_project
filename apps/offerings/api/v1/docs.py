from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)

from apps.offerings.api.v1.serializers import (
    OfferingCreateSerializer,
    OfferingReadSerializer,
    OfferingUpdateSerializer,
)

offering_list_create_schema = extend_schema_view(
    get=extend_schema(
        parameters=[
            # OpenApiParameter(
            #     name="category__id",
            #     description="Filter by category ID (UUID format)",
            #     required=False,
            #     type=OpenApiTypes.STR,
            # ),
            # OpenApiParameter(
            #     name="category__slug",
            #     description="Filter by category slug (e.g., dance)",
            #     required=False,
            #     type=OpenApiTypes.STR,
            # ),
            OpenApiParameter(
                name="search",
                description="Search in title, description, organization name, provider name, etc.",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="ordering",
                description="""Order by: created_at, title,
                price, duration_minutes (use - for descending)""",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="page",
                description="Page number",
                required=False,
                type=OpenApiTypes.INT,
            ),
            OpenApiParameter(
                name="page_size",
                description="Number of results per page",
                required=False,
                type=OpenApiTypes.INT,
            ),
        ],
        summary="List active offerings",
        description="Returns active offerings for active providers and active organizations.",
        responses={200: OfferingReadSerializer(many=True)},
        tags=["Offerings"],
    ),
    post=extend_schema(
        summary="Create offering",
        description="Creates a new offering for a provider inside an organization.",
        request=OfferingCreateSerializer,
        responses={
            201: OfferingReadSerializer,
            400: OpenApiResponse(description="Invalid offering data."),
            403: OpenApiResponse(description="Permission denied."),
        },
        tags=["Offerings"],
    ),
)


my_offerings_schema = extend_schema(
    summary="List my offerings",
    description="Returns offerings linked to provider profiles of the authenticated user.",
    responses={200: OfferingReadSerializer(many=True)},
    tags=["Offerings"],
)


organization_offerings_schema = extend_schema(
    summary="List organization offerings",
    description="Returns offerings of a specific organization.",
    parameters=[
        OpenApiParameter(
            name="organization_id",
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            required=True,
        )
    ],
    responses={
        200: OfferingReadSerializer(many=True),
        404: OpenApiResponse(description="Organization not found."),
    },
    tags=["Offerings"],
)


provider_offerings_schema = extend_schema(
    summary="List provider offerings",
    description="Returns offerings of a specific provider.",
    parameters=[
        OpenApiParameter(
            name="provider_id",
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            required=True,
        )
    ],
    responses={
        200: OfferingReadSerializer(many=True),
        404: OpenApiResponse(description="Provider not found."),
    },
    tags=["Offerings"],
)


offering_detail_schema = extend_schema_view(
    get=extend_schema(
        summary="Retrieve offering",
        responses={
            200: OfferingReadSerializer,
            404: OpenApiResponse(description="Offering not found."),
        },
        tags=["Offerings"],
    ),
    patch=extend_schema(
        summary="Update offering",
        request=OfferingUpdateSerializer,
        responses={
            200: OfferingReadSerializer,
            400: OpenApiResponse(description="Invalid offering data."),
            403: OpenApiResponse(description="Permission denied."),
            404: OpenApiResponse(description="Offering not found."),
        },
        tags=["Offerings"],
    ),
    put=extend_schema(
        summary="Update offering",
        request=OfferingUpdateSerializer,
        responses={
            200: OfferingReadSerializer,
            400: OpenApiResponse(description="Invalid offering data."),
            403: OpenApiResponse(description="Permission denied."),
            404: OpenApiResponse(description="Offering not found."),
        },
        tags=["Offerings"],
    ),
)
