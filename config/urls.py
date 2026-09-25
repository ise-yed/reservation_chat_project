from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # ── Admin Panel (standalone SPA) ──
    path("panel/", TemplateView.as_view(template_name="index.html"), name="admin-panel"),
    # ── API Schema ──
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/v1/auth/", include("apps.authentication.api.v1.urls")),
    path("api/v1/notifications/", include("apps.notifications.api.v1.urls")),
    path("api/v1/categories/", include("apps.categories.api.v1.urls")),
    path("api/v1/organizations/", include("apps.organizations.api.v1.urls")),
    path("api/v1/providers/", include("apps.providers.api.v1.urls")),
    path("api/v1/offerings/", include("apps.offerings.api.v1.urls")),
    path("api/v1/availability/", include("apps.availability.api.v1.urls")),
    path("api/v1/appointments/", include("apps.appointments.api.v1.urls")),
    path("api/v1/payments/", include("apps.payments.api.v1.urls")),
    path("api/v1/chat/", include("apps.chat.api.v1.urls")),
    # ── Admin panel API ──
    path("api/v1/admin/", include("apps.common.api.admin_urls")),
]
