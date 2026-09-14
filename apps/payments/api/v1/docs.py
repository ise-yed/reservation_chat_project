from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
)

from apps.payments.api.v1.serializers import (
    AppointmentPaymentCreateSerializer,
    PaymentMarkFailedSerializer,
    PaymentMarkPaidSerializer,
    PaymentReadSerializer,
    PaymentRefundSerializer,
)

appointment_payment_create_schema = extend_schema(
    summary="Initiate appointment payment",
    request=AppointmentPaymentCreateSerializer,
    responses={
        201: PaymentReadSerializer,
        200: PaymentReadSerializer,
        400: OpenApiResponse(description="Invalid payment data."),
        403: OpenApiResponse(description="Permission denied."),
    },
    tags=["Payments"],
)


my_payments_schema = extend_schema(
    summary="List my payments",
    responses={200: PaymentReadSerializer(many=True)},
    tags=["Payments"],
)


organization_payments_schema = extend_schema(
    summary="List organization payments",
    parameters=[
        OpenApiParameter(
            name="organization_id",
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            required=True,
        )
    ],
    responses={200: PaymentReadSerializer(many=True)},
    tags=["Payments"],
)


payment_detail_schema = extend_schema(
    summary="Retrieve payment",
    responses={
        200: PaymentReadSerializer,
        403: OpenApiResponse(description="Permission denied."),
        404: OpenApiResponse(description="Payment not found."),
    },
    tags=["Payments"],
)


payment_mark_paid_schema = extend_schema(
    summary="Mark payment as paid",
    request=PaymentMarkPaidSerializer,
    responses={200: PaymentReadSerializer},
    tags=["Payments"],
)


payment_mark_failed_schema = extend_schema(
    summary="Mark payment as failed",
    request=PaymentMarkFailedSerializer,
    responses={200: PaymentReadSerializer},
    tags=["Payments"],
)


payment_cancel_schema = extend_schema(
    summary="Cancel payment",
    responses={200: PaymentReadSerializer},
    tags=["Payments"],
)


payment_refund_schema = extend_schema(
    summary="Refund payment",
    request=PaymentRefundSerializer,
    responses={200: PaymentReadSerializer},
    tags=["Payments"],
)
