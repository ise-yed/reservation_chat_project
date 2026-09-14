from django.urls import path

from apps.appointments.api.v1.views import (
    AppointmentCancelView,
    AppointmentDetailView,
    AppointmentListCreateView,
    AppointmentStatusUpdateView,
    MyAppointmentListView,
    OrganizationAppointmentListView,
    ProviderAppointmentListView,
)

app_name = "appointments"

urlpatterns = [
    path("", AppointmentListCreateView.as_view(), name="list-create"),
    path("my/", MyAppointmentListView.as_view(), name="my-list"),
    path(
        "providers/<uuid:provider_id>/",
        ProviderAppointmentListView.as_view(),
        name="provider-list",
    ),
    path(
        "organizations/<uuid:organization_id>/",
        OrganizationAppointmentListView.as_view(),
        name="organization-list",
    ),
    path("<uuid:pk>/", AppointmentDetailView.as_view(), name="detail"),
    path("<uuid:pk>/cancel/", AppointmentCancelView.as_view(), name="cancel"),
    path("<uuid:pk>/status/", AppointmentStatusUpdateView.as_view(), name="status-update"),
]
