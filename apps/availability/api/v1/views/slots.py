from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.availability.api.v1.docs import available_slots_schema
from apps.availability.api.v1.serializers import (
    AvailableSlotQuerySerializer,
    AvailableSlotSerializer,
)
from apps.availability.services import get_available_slots


@available_slots_schema
class AvailableSlotView(APIView):
    """Get available time slots for a provider and offering."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query_serializer = AvailableSlotQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        slots = get_available_slots(
            provider_id=query_serializer.validated_data["provider_id"],
            offering_id=query_serializer.validated_data["offering_id"],
            target_date=query_serializer.validated_data["date"],
        )

        output_serializer = AvailableSlotSerializer(slots, many=True)

        return Response(
            {
                "date": query_serializer.validated_data["date"],
                "count": len(slots),
                "results": output_serializer.data,
            },
            status=status.HTTP_200_OK,
        )
