from django.urls import path

from apps.offerings.api.v1.views import (
    MyOfferingListView,
    OfferingDetailView,
    OfferingListCreateView,
    OrganizationOfferingListView,
    ProviderOfferingListView,
)

app_name = "offerings"

urlpatterns = [
    path("", OfferingListCreateView.as_view(), name="list-create"),
    path("my/", MyOfferingListView.as_view(), name="my-list"),
    path(
        "organizations/<uuid:organization_id>/",
        OrganizationOfferingListView.as_view(),
        name="organization-list",
    ),
    path(
        "providers/<uuid:provider_id>/",
        ProviderOfferingListView.as_view(),
        name="provider-list",
    ),
    path("<uuid:pk>/", OfferingDetailView.as_view(), name="detail"),
]
