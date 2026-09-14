from django.http import Http404
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter

from apps.audit.api.v1.docs import (
    audit_log_detail_schema,
    audit_log_list_schema,
    my_audit_logs_schema,
    organization_audit_logs_schema,
)
from apps.audit.api.v1.serializers import AuditLogReadSerializer
from apps.audit.models import AuditLog
from apps.audit.permissions import can_view_audit_log, can_view_organization_audit_logs
from apps.audit.selectors import (
    get_audit_log_by_id,
    get_organization_audit_logs,
    get_user_audit_logs,
    get_visible_audit_logs_for_user,
)
from apps.organizations.models import Organization
from apps.organizations.selectors import get_organization_by_id


@audit_log_detail_schema
class AuditLogDetailView(generics.RetrieveAPIView):
    """Retrieve audit log details."""

    serializer_class = AuditLogReadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> AuditLog:
        try:
            audit_log = get_audit_log_by_id(audit_log_id=self.kwargs["pk"])
        except AuditLog.DoesNotExist as exc:
            raise Http404 from exc

        if not can_view_audit_log(self.request.user, audit_log):
            raise PermissionDenied("You are not allowed to view this audit log.")

        return audit_log


@audit_log_list_schema
class AuditLogListView(generics.ListAPIView):
    """List audit logs visible to the authenticated user."""

    serializer_class = AuditLogReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "actor__email",
        "actor__first_name",
        "actor__last_name",
        "organization__name",
        "action",
        "status",
        "target_object_type",
        "target_object_id",
        "target_object_repr",
    ]
    ordering_fields = ["created_at", "action", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return get_visible_audit_logs_for_user(user=self.request.user)


@organization_audit_logs_schema
class OrganizationAuditLogListView(generics.ListAPIView):
    """List audit logs for a specific organization."""

    serializer_class = AuditLogReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "actor__email",
        "actor__first_name",
        "actor__last_name",
        "action",
        "status",
        "target_object_type",
        "target_object_id",
        "target_object_repr",
    ]
    ordering_fields = ["created_at", "action", "status"]
    ordering = ["-created_at"]

    def get_organization(self) -> Organization:
        try:
            return get_organization_by_id(
                organization_id=self.kwargs["organization_id"],
            )
        except Organization.DoesNotExist as exc:
            raise Http404 from exc

    def get_queryset(self):
        organization = self.get_organization()

        if not can_view_organization_audit_logs(self.request.user, organization):
            raise PermissionDenied("You are not allowed to view organization audit logs.")

        return get_organization_audit_logs(organization=organization)


@my_audit_logs_schema
class MyAuditLogListView(generics.ListAPIView):
    """List audit logs for the authenticated user."""

    serializer_class = AuditLogReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "action",
        "status",
        "target_object_type",
        "target_object_id",
        "target_object_repr",
    ]
    ordering_fields = ["created_at", "action", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return get_user_audit_logs(user=self.request.user)
