from django.urls import path

from apps.payments.api.v1.views import (
    AppointmentPaymentCreateView,
    MyPaymentListView,
    OrganizationPaymentListView,
    PaymentCancelView,
    PaymentDetailView,
    PaymentMarkFailedView,
    PaymentMarkPaidView,
    PaymentRefundView,
)

app_name = "payments"

urlpatterns = [
    path(
        "appointments/", AppointmentPaymentCreateView.as_view(), name="appointment-payment-create"
    ),
    path("my/", MyPaymentListView.as_view(), name="my-list"),
    path(
        "organizations/<uuid:organization_id>/",
        OrganizationPaymentListView.as_view(),
        name="organization-list",
    ),
    path("<uuid:pk>/", PaymentDetailView.as_view(), name="detail"),
    path("<uuid:pk>/mark-paid/", PaymentMarkPaidView.as_view(), name="mark-paid"),
    path("<uuid:pk>/mark-failed/", PaymentMarkFailedView.as_view(), name="mark-failed"),
    path("<uuid:pk>/cancel/", PaymentCancelView.as_view(), name="cancel"),
    path("<uuid:pk>/refund/", PaymentRefundView.as_view(), name="refund"),
]
