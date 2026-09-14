from django.urls import path

from apps.organizations.api.v1.views import (
    BranchDetailView,
    BranchListCreateView,
    MyOrganizationListView,
    OrganizationDetailView,
    OrganizationListCreateView,
)

app_name = "organizations"

urlpatterns = [
    path("", OrganizationListCreateView.as_view(), name="list-create"),
    path("my/", MyOrganizationListView.as_view(), name="my-list"),
    path("<uuid:pk>/", OrganizationDetailView.as_view(), name="detail"),
    path(
        "<uuid:organization_id>/branches/",
        BranchListCreateView.as_view(),
        name="branch-list-create",
    ),
    path(
        "branches/<uuid:pk>/",
        BranchDetailView.as_view(),
        name="branch-detail",
    ),
]
