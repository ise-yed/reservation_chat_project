from rest_framework import serializers

from apps.payments.models import Payment


class PaymentReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "appointment",
            "amount",
            "method",
            "status",
            "paid_at",
            "created_at",
        )
        read_only_fields = fields
