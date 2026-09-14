from django.urls import path

from apps.providers.api.v1.views import (
    MyProviderProfileListView,
    OrganizationProviderListView,
    ProviderProfileDetailView,
    ProviderProfileListCreateView,
)

app_name = "providers"

urlpatterns = [
    path("", ProviderProfileListCreateView.as_view(), name="list-create"),
    path("my/", MyProviderProfileListView.as_view(), name="my-list"),
    path(
        "organizations/<uuid:organization_id>/",
        OrganizationProviderListView.as_view(),
        name="organization-list",
    ),
    path("<uuid:pk>/", ProviderProfileDetailView.as_view(), name="detail"),
]
