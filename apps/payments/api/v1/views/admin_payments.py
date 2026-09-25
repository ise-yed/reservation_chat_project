"""
Admin payment views:
- List all payments for an organization
- Refund a payment
"""
from django.utils import timezone
from rest_framework import filters, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework.exceptions import PermissionDenied
from apps.common.permissions import IsAdminUser, get_user_org_ids
from apps.payments.api.v1.serializers import PaymentReadSerializer
from apps.payments.enums import PaymentStatus
from apps.payments.models import Payment


class OrgPaymentListView(generics.ListAPIView):
    """
    GET /api/v1/payments/organizations/{org_id}/
    Lists all payments for a given organization. Admin only.
    """

    permission_classes = [IsAdminUser]
    serializer_class = PaymentReadSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at", "amount", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        org_id = self.kwargs["org_id"]
        
        # Scope isolation
        allowed_orgs = get_user_org_ids(self.request.user)
        if allowed_orgs is not None and org_id not in allowed_orgs:
            raise PermissionDenied("You do not have access to this organization.")

        qs = Payment.objects.select_related(
            "appointment__organization",
            "appointment__customer",
            "appointment__provider__user",
        ).filter(appointment__organization_id=org_id)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class PaymentRefundView(APIView):
    """
    POST /api/v1/payments/{id}/refund/
    Marks a payment as refunded. Admin only.
    In a real integration, call the payment gateway here before updating status.
    """

    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        try:
            payment = Payment.objects.select_related("appointment").get(pk=pk)
        except Payment.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        # Scope isolation
        allowed_orgs = get_user_org_ids(request.user)
        if allowed_orgs is not None and payment.appointment.organization_id not in allowed_orgs:
            return Response({"detail": "You do not have permission to refund this payment."}, status=status.HTTP_403_FORBIDDEN)

        if payment.status != PaymentStatus.PAID:
            return Response(
                {"detail": f"Cannot refund a payment with status '{payment.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # TODO: integrate with gateway (e.g. zarinpal refund API) before flipping status
        payment.status = PaymentStatus.REFUNDED
        payment.save(update_fields=["status", "updated_at"])

        return Response(PaymentReadSerializer(payment).data, status=status.HTTP_200_OK)
