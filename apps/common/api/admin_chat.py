"""
Read-only Admin endpoints for monitoring chat conversations and messages.
Does NOT modify or interfere with the mobile app's /api/v1/chat/ endpoints.
"""
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import filters, generics

from apps.chat.api.v1.serializers.chat import (
    ConversationReadSerializer,
    MessageReadSerializer,
)
from apps.chat.models import Conversation, Message
from apps.common.permissions import IsAdminUser, get_user_org_ids


class AdminConversationListView(generics.ListAPIView):
    """
    GET /api/v1/admin/conversations/
    Read-only list of conversations for the admin panel.
    Scoped to organization(s) for org_admin/staff; global for super_admin.
    """

    permission_classes = [IsAdminUser]
    serializer_class = ConversationReadSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "customer__email",
        "customer__first_name",
        "customer__last_name",
        "customer__phone_number",
        "provider__email",
        "provider__first_name",
        "provider__last_name",
        "provider__phone_number",
    ]
    ordering_fields = ["updated_at", "created_at"]
    ordering = ["-updated_at"]

    def get_queryset(self):
        qs = Conversation.objects.select_related(
            "customer",
            "provider",
            "last_message",
            "last_message__sender",
            "patient_last_read_message",
            "doctor_last_read_message",
        ).order_by("-updated_at")

        allowed_orgs = get_user_org_ids(self.request.user)
        if allowed_orgs is not None:
            qs = qs.filter(
                Q(provider__provider_profiles__organization_id__in=allowed_orgs)
                | Q(appointments__organization_id__in=allowed_orgs)
            ).distinct()

        return qs


class AdminConversationMessageListView(generics.ListAPIView):
    """
    GET /api/v1/admin/conversations/<uuid:conversation_id>/messages/
    Read-only message history for a specific conversation in the admin panel.
    """

    permission_classes = [IsAdminUser]
    serializer_class = MessageReadSerializer

    def get_queryset(self):
        conversation_id = self.kwargs["conversation_id"]
        conv_qs = Conversation.objects.all()

        allowed_orgs = get_user_org_ids(self.request.user)
        if allowed_orgs is not None:
            conv_qs = conv_qs.filter(
                Q(provider__provider_profiles__organization_id__in=allowed_orgs)
                | Q(appointments__organization_id__in=allowed_orgs)
            ).distinct()

        conversation = get_object_or_404(conv_qs, id=conversation_id)
        return (
            Message.objects.filter(conversation=conversation)
            .select_related("sender")
            .order_by("-created_at")
        )