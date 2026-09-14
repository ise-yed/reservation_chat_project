from django.urls import path

from apps.audit.api.v1.views import (
    AuditLogDetailView,
    AuditLogListView,
    MyAuditLogListView,
    OrganizationAuditLogListView,
)

app_name = "audit"

urlpatterns = [
    path("", AuditLogListView.as_view(), name="list"),
    path("my/", MyAuditLogListView.as_view(), name="my-list"),
    path(
        "organizations/<uuid:organization_id>/",
        OrganizationAuditLogListView.as_view(),
        name="organization-list",
    ),
    path("<uuid:pk>/", AuditLogDetailView.as_view(), name="detail"),
]
