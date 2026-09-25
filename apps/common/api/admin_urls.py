from django.urls import include, path

from apps.common.api.dashboard import DashboardStatsView
from apps.notifications.api.v1.views.admin_deliveries import AdminNotificationDeliveryListView

urlpatterns = [
    # User management  GET/POST /api/v1/admin/users/   PATCH /api/v1/admin/users/{id}/
    path("users/", include("apps.users.api.v1.urls")),
    # Dashboard aggregate stats
    path("dashboard/stats/", DashboardStatsView.as_view(), name="admin-dashboard-stats"),
    # Notification delivery logs
    path(
        "notification-deliveries/",
        AdminNotificationDeliveryListView.as_view(),
        name="admin-notification-deliveries",
    ),
]
