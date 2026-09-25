from django.urls import path

from apps.payments.api.v1.views import (
    MyPaymentListView,
    PaymentCallbackView,
    PaymentDetailView,
    PaymentMarkPaidView,
    PaymentPayView,
)
from apps.payments.api.v1.views.admin_payments import OrgPaymentListView, PaymentRefundView

app_name = "payments"

urlpatterns = [
    path("my/", MyPaymentListView.as_view(), name="my-list"),
    path("<uuid:pk>/", PaymentDetailView.as_view(), name="detail"),
    path("<uuid:pk>/pay/", PaymentPayView.as_view(), name="pay"),
    path("<uuid:pk>/callback/", PaymentCallbackView.as_view(), name="callback"),
    path("<uuid:pk>/mark-paid/", PaymentMarkPaidView.as_view(), name="mark-paid"),
    # Admin endpoints
    path("<uuid:pk>/refund/", PaymentRefundView.as_view(), name="refund"),
    path("organizations/<uuid:org_id>/", OrgPaymentListView.as_view(), name="org-list"),
]
