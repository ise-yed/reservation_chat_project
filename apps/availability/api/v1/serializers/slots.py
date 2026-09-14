from rest_framework import serializers


class AvailableSlotQuerySerializer(serializers.Serializer):
    """Serializer for querying available slots."""

    provider_id = serializers.UUIDField()
    offering_id = serializers.UUIDField()
    date = serializers.DateField()


class AvailableSlotSerializer(serializers.Serializer):
    """Serializer for available time slot response."""

    provider_id = serializers.UUIDField()
    offering_id = serializers.UUIDField()
    start_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField()
    blocked_start_at = serializers.DateTimeField()
    blocked_end_at = serializers.DateTimeField()
    duration_minutes = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
