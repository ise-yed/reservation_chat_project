from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)

from apps.availability.api.v1.serializers import (
    AvailableSlotSerializer,
    HolidayCreateSerializer,
    HolidayReadSerializer,
    HolidayUpdateSerializer,
    TimeOffCreateSerializer,
    TimeOffReadSerializer,
    TimeOffUpdateSerializer,
    WorkingHourCreateSerializer,
    WorkingHourReadSerializer,
    WorkingHourUpdateSerializer,
)

working_hour_list_create_schema = extend_schema_view(
    get=extend_schema(
        summary="List active working hours",
        responses={200: WorkingHourReadSerializer(many=True)},
        tags=["Availability - Working Hours"],
    ),
    post=extend_schema(
        summary="Create working hour",
        request=WorkingHourCreateSerializer,
        responses={
            201: WorkingHourReadSerializer,
            400: OpenApiResponse(description="Invalid working hour data."),
            403: OpenApiResponse(description="Permission denied."),
        },
        tags=["Availability - Working Hours"],
    ),
)


working_hour_detail_schema = extend_schema_view(
    get=extend_schema(
        summary="Retrieve working hour",
        responses={200: WorkingHourReadSerializer},
        tags=["Availability - Working Hours"],
    ),
    patch=extend_schema(
        summary="Update working hour",
        request=WorkingHourUpdateSerializer,
        responses={200: WorkingHourReadSerializer},
        tags=["Availability - Working Hours"],
    ),
    put=extend_schema(
        summary="Update working hour",
        request=WorkingHourUpdateSerializer,
        responses={200: WorkingHourReadSerializer},
        tags=["Availability - Working Hours"],
    ),
)


provider_working_hours_schema = extend_schema(
    summary="List provider working hours",
    parameters=[
        OpenApiParameter(
            name="provider_id",
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            required=True,
        )
    ],
    responses={200: WorkingHourReadSerializer(many=True)},
    tags=["Availability - Working Hours"],
)


time_off_list_create_schema = extend_schema_view(
    get=extend_schema(
        summary="List active time offs",
        responses={200: TimeOffReadSerializer(many=True)},
        tags=["Availability - Time Offs"],
    ),
    post=extend_schema(
        summary="Create time off",
        request=TimeOffCreateSerializer,
        responses={201: TimeOffReadSerializer},
        tags=["Availability - Time Offs"],
    ),
)


time_off_detail_schema = extend_schema_view(
    get=extend_schema(
        summary="Retrieve time off",
        responses={200: TimeOffReadSerializer},
        tags=["Availability - Time Offs"],
    ),
    patch=extend_schema(
        summary="Update time off",
        request=TimeOffUpdateSerializer,
        responses={200: TimeOffReadSerializer},
        tags=["Availability - Time Offs"],
    ),
    put=extend_schema(
        summary="Update time off",
        request=TimeOffUpdateSerializer,
        responses={200: TimeOffReadSerializer},
        tags=["Availability - Time Offs"],
    ),
)


provider_time_offs_schema = extend_schema(
    summary="List provider time offs",
    parameters=[
        OpenApiParameter(
            name="provider_id",
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            required=True,
        )
    ],
    responses={200: TimeOffReadSerializer(many=True)},
    tags=["Availability - Time Offs"],
)


holiday_list_create_schema = extend_schema_view(
    get=extend_schema(
        summary="List active holidays",
        responses={200: HolidayReadSerializer(many=True)},
        tags=["Availability - Holidays"],
    ),
    post=extend_schema(
        summary="Create organization holiday",
        request=HolidayCreateSerializer,
        responses={201: HolidayReadSerializer},
        tags=["Availability - Holidays"],
    ),
)


holiday_detail_schema = extend_schema_view(
    get=extend_schema(
        summary="Retrieve holiday",
        responses={200: HolidayReadSerializer},
        tags=["Availability - Holidays"],
    ),
    patch=extend_schema(
        summary="Update holiday",
        request=HolidayUpdateSerializer,
        responses={200: HolidayReadSerializer},
        tags=["Availability - Holidays"],
    ),
    put=extend_schema(
        summary="Update holiday",
        request=HolidayUpdateSerializer,
        responses={200: HolidayReadSerializer},
        tags=["Availability - Holidays"],
    ),
)


organization_holidays_schema = extend_schema(
    summary="List organization holidays",
    parameters=[
        OpenApiParameter(
            name="organization_id",
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            required=True,
        )
    ],
    responses={200: HolidayReadSerializer(many=True)},
    tags=["Availability - Holidays"],
)


available_slots_schema = extend_schema(
    summary="Get available slots",
    description="Returns available slots for a provider, offering and date.",
    parameters=[
        OpenApiParameter("provider_id", OpenApiTypes.UUID, OpenApiParameter.QUERY, required=True),
        OpenApiParameter("offering_id", OpenApiTypes.UUID, OpenApiParameter.QUERY, required=True),
        OpenApiParameter("date", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=True),
    ],
    responses={200: AvailableSlotSerializer(many=True)},
    tags=["Availability - Slots"],
)
