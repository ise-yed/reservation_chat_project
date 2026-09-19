# urls.py
from django.urls import path

from apps.notifications.api.v1.views import (
    FCMDeviceRegisterView,
    NotificationDetailView,
    NotificationListView,
    NotificationMarkAllAsReadView,
    NotificationMarkAsReadView,
)

app_name = "notifications"

urlpatterns = [
    path("", NotificationListView.as_view(), name="list"),
    path("<uuid:pk>/", NotificationDetailView.as_view(), name="detail"),
    path("<uuid:pk>/mark-read/", NotificationMarkAsReadView.as_view(), name="mark-read"),
    path("mark-all-read/", NotificationMarkAllAsReadView.as_view(), name="mark-all-read"),
    path("devices/register/", FCMDeviceRegisterView.as_view(), name="device-register"),  # <--- اضافه شد
]
