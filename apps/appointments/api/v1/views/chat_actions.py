from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.appointments.api.v1.docs import (
    appointment_chat_access_schema,
    appointment_complete_schema,
)
from apps.appointments.models import Appointment
from apps.appointments.services.chat_lifecycle import (
    complete_appointment_visit,
    get_chat_access_status,
)


class AppointmentChatAccessView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @appointment_chat_access_schema
    def get(self, request, appointment_id):
        appointment = get_object_or_404(
            Appointment.objects.select_related("provider__user", "customer").filter(
                Q(customer=request.user) | Q(provider__user=request.user)
            ),
            id=appointment_id
        )
        data = get_chat_access_status(appointment=appointment, user=request.user)
        return Response(data, status=status.HTTP_200_OK)


class AppointmentCompleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @appointment_complete_schema
    def post(self, request, appointment_id):
        appointment = get_object_or_404(
            Appointment.objects.select_related("provider__user", "customer"),
            id=appointment_id
        )
        complete_appointment_visit(appointment=appointment, actor=request.user)
        return Response({"message": "Appointment completed successfully."}, status=status.HTTP_200_OK)