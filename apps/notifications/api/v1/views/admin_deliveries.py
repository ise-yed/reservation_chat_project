"""
Admin view for NotificationDelivery log.
GET /api/v1/admin/notification-deliveries/
"""
from rest_framework import filters, generics
from rest_framework import serializers as drf_serializers

from apps.common.permissions import IsAdminUser
from apps.notifications.models import NotificationDelivery


class NotificationDeliverySerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = NotificationDelivery
        fields = (
            "id",
            "user",
            "channel",
            "type",
            "recipient",
            "subject",
            "status",
            "error_message",
            "sent_at",
            "created_at",
        )
        read_only_fields = fields


class AdminNotificationDeliveryListView(generics.ListAPIView):
    """
    GET /api/v1/admin/notification-deliveries/
    Supports ?channel=email|push|sms  ?status=sent|failed|pending
    """

    permission_classes = [IsAdminUser]
    serializer_class = NotificationDeliverySerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ["recipient", "subject"]
    ordering_fields = ["created_at", "sent_at", "status", "channel"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = NotificationDelivery.objects.select_related("user")
        channel = self.request.query_params.get("channel")
        status_filter = self.request.query_params.get("status")
        if channel:
            qs = qs.filter(channel=channel)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs
