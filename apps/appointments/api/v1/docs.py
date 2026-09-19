from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)

from apps.appointments.api.v1.serializers import (
    AppointmentCancelSerializer,
    AppointmentCreateSerializer,
    AppointmentReadSerializer,
    AppointmentStatusUpdateSerializer,
)

appointment_list_create_schema = extend_schema_view(
    get=extend_schema(
        summary="List appointments",
        description="Returns appointments visible to the authenticated user.",
        responses={200: AppointmentReadSerializer(many=True)},
        tags=["Appointments"],
    ),
    post=extend_schema(
        summary="Create appointment",
        description="Creates a new appointment for the authenticated customer.",
        request=AppointmentCreateSerializer,
        responses={
            201: AppointmentReadSerializer,
            400: OpenApiResponse(description="Invalid appointment data."),
            403: OpenApiResponse(description="Permission denied."),
        },
        tags=["Appointments"],
    ),
)


my_appointments_schema = extend_schema(
    summary="List my appointments",
    description="Returns appointments where the authenticated user is the customer.",
    responses={200: AppointmentReadSerializer(many=True)},
    tags=["Appointments"],
)


provider_appointments_schema = extend_schema(
    summary="List provider appointments",
    parameters=[
        OpenApiParameter(
            name="provider_id",
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            required=True,
        )
    ],
    responses={200: AppointmentReadSerializer(many=True)},
    tags=["Appointments"],
)


organization_appointments_schema = extend_schema(
    summary="List organization appointments",
    parameters=[
        OpenApiParameter(
            name="organization_id",
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            required=True,
        )
    ],
    responses={200: AppointmentReadSerializer(many=True)},
    tags=["Appointments"],
)


appointment_detail_schema = extend_schema(
    summary="Retrieve appointment",
    responses={
        200: AppointmentReadSerializer,
        403: OpenApiResponse(description="Permission denied."),
        404: OpenApiResponse(description="Appointment not found."),
    },
    tags=["Appointments"],
)


appointment_cancel_schema = extend_schema(
    summary="Cancel appointment",
    request=AppointmentCancelSerializer,
    responses={
        200: AppointmentReadSerializer,
        400: OpenApiResponse(description="Appointment cannot be cancelled."),
        403: OpenApiResponse(description="Permission denied."),
        404: OpenApiResponse(description="Appointment not found."),
    },
    tags=["Appointments"],
)


appointment_status_schema = extend_schema(
    summary="Update appointment status",
    request=AppointmentStatusUpdateSerializer,
    responses={
        200: AppointmentReadSerializer,
        400: OpenApiResponse(description="Invalid status transition."),
        403: OpenApiResponse(description="Permission denied."),
        404: OpenApiResponse(description="Appointment not found."),
    },
    tags=["Appointments"],

)


appointment_chat_access_schema = extend_schema(
    summary="Get Chat Access Status",
    description="Returns the chat access rules and current status for a specific appointment.",
    responses={
        200: OpenApiResponse(description="Chat access details."),
        404: OpenApiResponse(description="Appointment not found or not participant.")
    },
    tags=["Appointments (Chat)"]
)

appointment_complete_schema = extend_schema(
    summary="Complete Appointment Visit",
    description="Manually end an online chat visit by the doctor. Freezes the patient's chat capability.",
    responses={
        200: OpenApiResponse(description="Appointment completed successfully."),
        400: OpenApiResponse(description="Validation error (e.g., not online, not confirmed)."),
        403: OpenApiResponse(description="Permission denied (Only doctor can complete)."),
    },
    tags=["Appointments (Chat)"]
)
