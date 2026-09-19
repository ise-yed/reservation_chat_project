from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.payments.api.v1.serializers import PaymentReadSerializer
from apps.payments.models import Payment
from apps.payments.permissions import can_view_payment
from apps.payments.services import (
    build_callback_url,
    mark_paid_in_person,
    start_online_payment,
    verify_online_payment,
)


class MyPaymentListView(generics.ListAPIView):
    serializer_class = PaymentReadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(appointment__customer=self.request.user)


class PaymentDetailView(generics.RetrieveAPIView):
    serializer_class = PaymentReadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        try:
            payment = Payment.objects.select_related(
                "appointment__provider__user", "appointment__organization"
            ).get(id=self.kwargs["pk"])
        except Payment.DoesNotExist as exc:
            raise Http404 from exc
        if not can_view_payment(self.request.user, payment):
            raise Http404
        return payment


class PaymentPayView(APIView):
    """Start / retry an online payment. Returns the gateway URL."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            payment, pay_url = start_online_payment(
                payment_id=pk,
                actor=request.user,
                callback_url=build_callback_url(request, pk),
            )
        except Payment.DoesNotExist as exc:
            raise Http404 from exc
        data = dict(PaymentReadSerializer(payment).data)
        data["pay_url"] = pay_url
        return Response(data, status=status.HTTP_200_OK)


class PaymentCallbackView(APIView):
    """Gateway redirects here. No JWT: the result is verified server-side with the gateway."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request, pk):
        params = request.query_params.dict()
        params.update({k: v for k, v in request.data.items()})
        try:
            payment = verify_online_payment(payment_id=pk, params=params)
        except Payment.DoesNotExist as exc:
            raise Http404 from exc

        return_url = getattr(settings, "PAYMENT_RETURN_URL", "")
        if return_url:  # e.g. a Flutter deep link
            return redirect(f"{return_url}?payment_id={payment.id}&status={payment.status}")
        return Response(
            {
                "payment_id": str(payment.id),
                "status": payment.status,
                "appointment_id": str(payment.appointment_id),
                "appointment_status": payment.appointment.status,
            }
        )

    post = get


class PaymentMarkPaidView(APIView):
    """Provider/staff: patient paid at the clinic."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            payment = mark_paid_in_person(payment_id=pk, actor=request.user)
        except Payment.DoesNotExist as exc:
            raise Http404 from exc
        return Response(PaymentReadSerializer(payment).data, status=status.HTTP_200_OK)
