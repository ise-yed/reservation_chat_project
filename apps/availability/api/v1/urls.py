from django.urls import path

from apps.availability.api.v1.views import (
    AvailableSlotView,
    HolidayDetailView,
    HolidayListCreateView,
    OrganizationHolidayListView,
    ProviderTimeOffListView,
    ProviderWorkingHourListView,
    TimeOffDetailView,
    TimeOffListCreateView,
    WorkingHourDetailView,
    WorkingHourListCreateView,
)

app_name = "availability"

urlpatterns = [
    path("working-hours/", WorkingHourListCreateView.as_view(), name="working-hour-list-create"),
    path("working-hours/<uuid:pk>/", WorkingHourDetailView.as_view(), name="working-hour-detail"),
    path(
        "providers/<uuid:provider_id>/working-hours/",
        ProviderWorkingHourListView.as_view(),
        name="provider-working-hour-list",
    ),
    path("time-offs/", TimeOffListCreateView.as_view(), name="time-off-list-create"),
    path("time-offs/<uuid:pk>/", TimeOffDetailView.as_view(), name="time-off-detail"),
    path(
        "providers/<uuid:provider_id>/time-offs/",
        ProviderTimeOffListView.as_view(),
        name="provider-time-off-list",
    ),
    path("holidays/", HolidayListCreateView.as_view(), name="holiday-list-create"),
    path("holidays/<uuid:pk>/", HolidayDetailView.as_view(), name="holiday-detail"),
    path(
        "organizations/<uuid:organization_id>/holidays/",
        OrganizationHolidayListView.as_view(),
        name="organization-holiday-list",
    ),
    path("slots/", AvailableSlotView.as_view(), name="available-slots"),
]
