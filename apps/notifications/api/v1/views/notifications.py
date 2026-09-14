import uuid

from django.http import Http404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.api.v1.docs import (
    notification_detail_schema,
    notification_list_schema,
    notification_mark_all_as_read_schema,
    notification_mark_as_read_schema,
)
from apps.notifications.api.v1.serializers import NotificationSerializer
from apps.notifications.models import Notification
from apps.notifications.selectors import (
    get_user_notification_by_id,
    get_user_notifications,
)
from apps.notifications.services import (
    mark_all_notifications_as_read,
    mark_notification_as_read,
)


@notification_list_schema
class NotificationListView(generics.ListAPIView):
    """List notifications for the authenticated user."""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()

        return get_user_notifications(user=self.request.user)


@notification_detail_schema
class NotificationDetailView(generics.RetrieveAPIView):
    """Retrieve a single notification belonging to the authenticated user."""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> Notification:
        try:
            pk = self.kwargs["pk"]
            if isinstance(pk, uuid.UUID):
                pk = str(pk)
            return get_user_notification_by_id(
                user=self.request.user,
                notification_id=pk,
            )
        except Notification.DoesNotExist as exc:
            raise Http404 from exc


@notification_mark_as_read_schema
class NotificationMarkAsReadView(APIView):
    """Mark a single notification as read for the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk: int, *args, **kwargs):
        try:
            notification = get_user_notification_by_id(
                user=request.user,
                notification_id=pk,
            )
        except Notification.DoesNotExist as exc:
            raise Http404 from exc

        notification = mark_notification_as_read(notification=notification)
        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)


@notification_mark_all_as_read_schema
class NotificationMarkAllAsReadView(APIView):
    """Mark all notifications as read for the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        updated_count = mark_all_notifications_as_read(user=request.user)
        return Response(
            {"marked_as_read": updated_count},
            status=status.HTTP_200_OK,
        )
