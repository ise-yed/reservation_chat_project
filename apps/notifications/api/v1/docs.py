from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.notifications.api.v1.serializers import FCMDeviceSerializer, NotificationSerializer

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


fcm_device_register_schema = extend_schema(
    summary="Register Device for Push Notifications",
    description="Register or update Firebase Cloud Messaging (FCM) token for the current user.",
    request=FCMDeviceSerializer,
    responses={200: OpenApiResponse(description="Device registered successfully.")},
    tags=["Notifications"],
)
