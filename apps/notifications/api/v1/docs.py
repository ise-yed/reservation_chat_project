from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.notifications.api.v1.serializers import NotificationSerializer

notification_list_schema = extend_schema(
    responses={200: NotificationSerializer(many=True)},
    tags=["Notifications"],
)

notification_detail_schema = extend_schema(
    responses={
        200: NotificationSerializer,
        404: OpenApiResponse(description="Notification not found."),
    },
    tags=["Notifications"],
)

notification_mark_as_read_schema = extend_schema(
    responses={
        200: NotificationSerializer,
        404: OpenApiResponse(description="Notification not found."),
    },
    tags=["Notifications"],
)

notification_mark_all_as_read_schema = extend_schema(
    responses={200: OpenApiResponse(description="All notifications marked as read.")},
    tags=["Notifications"],
)
