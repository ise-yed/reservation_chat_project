from django.urls import path

from apps.users.api.v1.views.admin_users import AdminUserDetailView, AdminUserListCreateView

app_name = "admin_users"

urlpatterns = [
    path("", AdminUserListCreateView.as_view(), name="list-create"),
    path("<uuid:pk>/", AdminUserDetailView.as_view(), name="detail"),
]
