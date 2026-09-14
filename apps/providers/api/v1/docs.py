from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)

from apps.providers.api.v1.serializers import (
    ProviderProfileCreateSerializer,
    ProviderProfileReadSerializer,
    ProviderProfileUpdateSerializer,
)

provider_list_create_schema = extend_schema_view(
    get=extend_schema(
        summary="List active providers",
        description="Returns active providers in active organizations.",
        responses={200: ProviderProfileReadSerializer(many=True)},
        tags=["Providers"],
    ),
    post=extend_schema(
        summary="Create provider profile",
        description=(
            "Creates a provider profile inside an organization."
            " Only organization owner or super admin can create it."
        ),
        request=ProviderProfileCreateSerializer,
        responses={
            201: ProviderProfileReadSerializer,
            400: OpenApiResponse(description="Invalid provider data."),
            403: OpenApiResponse(description="Permission denied."),
        },
        tags=["Providers"],
    ),
)


my_provider_profiles_schema = extend_schema(
    summary="List my provider profiles",
    description="Returns provider profiles linked to the authenticated user.",
    responses={200: ProviderProfileReadSerializer(many=True)},
    tags=["Providers"],
)


organization_providers_schema = extend_schema(
    summary="List organization providers",
    description="Returns providers of a specific organization.",
    parameters=[
        OpenApiParameter(
            name="organization_id",
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            required=True,
        )
    ],
    responses={
        200: ProviderProfileReadSerializer(many=True),
        404: OpenApiResponse(description="Organization not found."),
    },
    tags=["Providers"],
)


provider_detail_schema = extend_schema_view(
    get=extend_schema(
        summary="Retrieve provider profile",
        responses={
            200: ProviderProfileReadSerializer,
            404: OpenApiResponse(description="Provider profile not found."),
        },
        tags=["Providers"],
    ),
    patch=extend_schema(
        summary="Update provider profile",
        request=ProviderProfileUpdateSerializer,
        responses={
            200: ProviderProfileReadSerializer,
            400: OpenApiResponse(description="Invalid provider data."),
            403: OpenApiResponse(description="Permission denied."),
            404: OpenApiResponse(description="Provider profile not found."),
        },
        tags=["Providers"],
    ),
    put=extend_schema(
        summary="Update provider profile",
        request=ProviderProfileUpdateSerializer,
        responses={
            200: ProviderProfileReadSerializer,
            400: OpenApiResponse(description="Invalid provider data."),
            403: OpenApiResponse(description="Permission denied."),
            404: OpenApiResponse(description="Provider profile not found."),
        },
        tags=["Providers"],
    ),
)
