from django.http import Http404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.appointments.api.v1.docs import (
    appointment_cancel_schema,
    appointment_detail_schema,
    appointment_list_create_schema,
    appointment_status_schema,
    my_appointments_schema,
    organization_appointments_schema,
    provider_appointments_schema,
)
from apps.appointments.api.v1.serializers import (
    AppointmentCancelSerializer,
    AppointmentCreateSerializer,
    AppointmentReadSerializer,
    AppointmentStatusUpdateSerializer,
)
from apps.appointments.models import Appointment
from apps.appointments.permissions import CanViewOrManageAppointment
from apps.appointments.selectors import (
    get_appointment_by_id,
    get_organization_appointments,
    get_provider_appointments,
    get_user_appointments,
)
from apps.appointments.services import (
    cancel_appointment,
    create_appointment,
    update_appointment_status,
)
from apps.organizations.models import Organization
from apps.organizations.permissions import can_manage_organization
from apps.organizations.selectors import get_organization_by_id
from apps.providers.models import ProviderProfile
from apps.providers.selectors import get_provider_by_id


@appointment_cancel_schema
class AppointmentCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            appointment = get_appointment_by_id(appointment_id=pk)
        except Appointment.DoesNotExist as exc:
            raise Http404 from exc

        serializer = AppointmentCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        appointment = cancel_appointment(
            appointment=appointment,
            actor=request.user,
            **serializer.validated_data,
        )

        output_serializer = AppointmentReadSerializer(appointment)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


@appointment_detail_schema
class AppointmentDetailView(generics.RetrieveAPIView):
    serializer_class = AppointmentReadSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        CanViewOrManageAppointment,
    ]

    def get_object(self) -> Appointment:
        try:
            appointment = get_appointment_by_id(
                appointment_id=self.kwargs["pk"],
            )
        except Appointment.DoesNotExist as exc:
            raise Http404 from exc

        self.check_object_permissions(self.request, appointment)
        return appointment


@appointment_list_create_schema
class AppointmentListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "customer__email",
        "customer__first_name",
        "customer__last_name",
        "provider__user__email",
        "provider__user__first_name",
        "provider__user__last_name",
        "offering__title",
        "organization__name",
    ]
    ordering_fields = ["start_at", "created_at", "status"]
    ordering = ["-start_at"]

    def get_queryset(self):
        user = self.request.user

        queryset = Appointment.objects.select_related(
            "organization",
            "branch",
            "customer",
            "provider",
            "provider__user",
            "offering",
        ).order_by("-start_at")

        if user.is_superuser:
            return queryset

        return queryset.filter(customer=user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AppointmentCreateSerializer
        return AppointmentReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = AppointmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        appointment = create_appointment(
            customer=request.user,
            **serializer.validated_data,
        )

        output_serializer = AppointmentReadSerializer(appointment)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@appointment_status_schema
class AppointmentStatusUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            appointment = get_appointment_by_id(appointment_id=pk)
        except Appointment.DoesNotExist as exc:
            raise Http404 from exc

        serializer = AppointmentStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        appointment = update_appointment_status(
            appointment=appointment,
            actor=request.user,
            status=serializer.validated_data["status"],
        )

        output_serializer = AppointmentReadSerializer(appointment)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


@my_appointments_schema
class MyAppointmentListView(generics.ListAPIView):
    serializer_class = AppointmentReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "provider__user__email",
        "provider__user__first_name",
        "provider__user__last_name",
        "offering__title",
        "organization__name",
    ]
    ordering_fields = ["start_at", "created_at", "status"]
    ordering = ["-start_at"]

    def get_queryset(self):
        return get_user_appointments(user=self.request.user)


@provider_appointments_schema
class ProviderAppointmentListView(generics.ListAPIView):
    serializer_class = AppointmentReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "customer__email",
        "customer__first_name",
        "customer__last_name",
        "offering__title",
        "status",
    ]
    ordering_fields = ["start_at", "created_at", "status"]
    ordering = ["-start_at"]

    def get_provider(self) -> ProviderProfile:
        try:
            return get_provider_by_id(provider_id=self.kwargs["provider_id"])
        except ProviderProfile.DoesNotExist as exc:
            raise Http404 from exc

    def get_queryset(self):
        provider = self.get_provider()
        user = self.request.user

        can_view = (
            user.is_superuser
            or provider.user_id == user.id
            or can_manage_organization(user, provider.organization)
        )

        if not can_view:
            raise PermissionDenied("You are not allowed to view this provider appointments.")

        return get_provider_appointments(provider=provider)


@organization_appointments_schema
class OrganizationAppointmentListView(generics.ListAPIView):
    serializer_class = AppointmentReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "customer__email",
        "customer__first_name",
        "customer__last_name",
        "provider__user__email",
        "provider__user__first_name",
        "provider__user__last_name",
        "offering__title",
        "status",
    ]
    ordering_fields = ["start_at", "created_at", "status"]
    ordering = ["-start_at"]

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
            raise PermissionDenied("You are not allowed to view this organization appointments.")

        return get_organization_appointments(organization=organization)
