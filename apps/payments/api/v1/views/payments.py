from django.http import Http404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organizations.models import Organization
from apps.organizations.permissions import can_manage_organization
from apps.organizations.selectors import get_organization_by_id
from apps.payments.api.v1.docs import (
    appointment_payment_create_schema,
    my_payments_schema,
    organization_payments_schema,
    payment_cancel_schema,
    payment_detail_schema,
    payment_mark_failed_schema,
    payment_mark_paid_schema,
    payment_refund_schema,
)
from apps.payments.api.v1.serializers import (
    AppointmentPaymentCreateSerializer,
    PaymentMarkFailedSerializer,
    PaymentMarkPaidSerializer,
    PaymentReadSerializer,
    PaymentRefundSerializer,
)
from apps.payments.models import Payment
from apps.payments.permissions import can_view_payment
from apps.payments.selectors import (
    get_organization_payments,
    get_payment_by_id,
    get_user_payments,
)
from apps.payments.services import (
    cancel_payment,
    initiate_appointment_payment,
    mark_payment_as_failed,
    mark_payment_as_paid,
    refund_payment,
)


class PaymentObjectMixin:
    """Mixin to get payment object by ID."""

    def get_payment(self, pk) -> Payment:
        try:
            return get_payment_by_id(payment_id=pk)
        except Payment.DoesNotExist as exc:
            raise Http404 from exc


@payment_mark_paid_schema
class PaymentMarkPaidView(PaymentObjectMixin, APIView):
    """Mark a payment as paid."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        payment = self.get_payment(pk)

        serializer = PaymentMarkPaidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = mark_payment_as_paid(
            payment=payment,
            actor=request.user,
            **serializer.validated_data,
        )

        output_serializer = PaymentReadSerializer(payment)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


@payment_mark_failed_schema
class PaymentMarkFailedView(PaymentObjectMixin, APIView):
    """Mark a payment as failed."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        payment = self.get_payment(pk)

        serializer = PaymentMarkFailedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = mark_payment_as_failed(
            payment=payment,
            actor=request.user,
            **serializer.validated_data,
        )

        output_serializer = PaymentReadSerializer(payment)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


@payment_cancel_schema
class PaymentCancelView(PaymentObjectMixin, APIView):
    """Cancel a payment."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        payment = self.get_payment(pk)

        payment = cancel_payment(
            payment=payment,
            actor=request.user,
        )

        output_serializer = PaymentReadSerializer(payment)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


@payment_refund_schema
class PaymentRefundView(PaymentObjectMixin, APIView):
    """Refund a payment."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        payment = self.get_payment(pk)

        serializer = PaymentRefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = refund_payment(
            payment=payment,
            actor=request.user,
            **serializer.validated_data,
        )

        output_serializer = PaymentReadSerializer(payment)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


@payment_detail_schema
class PaymentDetailView(generics.RetrieveAPIView):
    """Retrieve payment details."""

    serializer_class = PaymentReadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> Payment:
        try:
            payment = get_payment_by_id(payment_id=self.kwargs["pk"])
        except Payment.DoesNotExist as exc:
            raise Http404 from exc

        if not can_view_payment(self.request.user, payment):
            raise PermissionDenied("You are not allowed to view this payment.")

        return payment


@organization_payments_schema
class OrganizationPaymentListView(generics.ListAPIView):
    """List payments for a specific organization."""

    serializer_class = PaymentReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "payer__email",
        "payer__first_name",
        "payer__last_name",
        "appointment__offering__title",
        "gateway_reference",
        "status",
    ]
    ordering_fields = ["created_at", "amount", "status"]
    ordering = ["-created_at"]

    def get_organization(self) -> Organization:
        try:
            return get_organization_by_id(
                organization_id=self.kwargs["organization_id"],
            )
        except Organization.DoesNotExist as exc:
            raise Http404 from exc

    def get_queryset(self):
        organization = self.get_organization()

        if not can_manage_organization(self.request.user, organization):
            raise PermissionDenied("You are not allowed to view organization payments.")

        return get_organization_payments(organization=organization)


@my_payments_schema
class MyPaymentListView(generics.ListAPIView):
    """List payments for the authenticated user."""

    serializer_class = PaymentReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "appointment__offering__title",
        "organization__name",
        "gateway_reference",
        "status",
    ]
    ordering_fields = ["created_at", "amount", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return get_user_payments(user=self.request.user)


@appointment_payment_create_schema
class AppointmentPaymentCreateView(APIView):
    """Create a payment for an appointment."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AppointmentPaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = initiate_appointment_payment(
            actor=request.user,
            **serializer.validated_data,
        )

        output_serializer = PaymentReadSerializer(payment)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
