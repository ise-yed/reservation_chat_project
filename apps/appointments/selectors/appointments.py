from datetime import datetime, time

from django.db.models import QuerySet
from django.utils import timezone

from apps.appointments.enums import ACTIVE_APPOINTMENT_STATUSES
from apps.appointments.models import Appointment


def get_appointment_by_id(*, appointment_id) -> Appointment:
    return Appointment.objects.select_related(
        "organization",
        "branch",
        "customer",
        "provider",
        "provider__user",
        "provider__organization",
        "provider__branch",
        "offering",
        "created_by",
        "cancelled_by",
        "payment",
    ).get(id=appointment_id)



def get_provider_appointments_for_date(*, provider, target_date) -> QuerySet[Appointment]:
    """Get provider's active appointments overlapping a specific date, for slot conflict checks."""
    current_timezone = timezone.get_current_timezone()
    day_start = timezone.make_aware(
        datetime.combine(target_date, time.min),
        current_timezone,
    )
    day_end = timezone.make_aware(
        datetime.combine(target_date, time.max),
        current_timezone,
    )


    return (
        Appointment.objects
        .filter(
            provider=provider,
            status__in=ACTIVE_APPOINTMENT_STATUSES,
            blocked_start_at__lt=day_end,
            blocked_end_at__gt=day_start,
        )
        .order_by("blocked_start_at")
    )




def get_user_appointments(*, user) -> QuerySet[Appointment]:
    return (
        Appointment.objects.filter(customer=user)
        .select_related(
            "organization",
            "branch",
            "customer",
            "provider",
            "provider__user",
            "offering",
            "payment",
        )
        .order_by("-start_at")
    )



def get_provider_appointments(*, provider, include_cancelled: bool = True) -> QuerySet[Appointment]:
    queryset = (
        Appointment.objects.filter(provider=provider)
        .select_related(
            "organization",
            "branch",
            "customer",
            "provider",
            "provider__user",
            "offering",
            "payment",
        )
        .order_by("-start_at")
    )


    if not include_cancelled:
        queryset = queryset.exclude(
            status__in=[
                "cancelled_by_customer",
                "cancelled_by_provider",
            ]
        )


    return queryset



def get_organization_appointments(
    *,
    organization,
    include_cancelled: bool = True,
) -> QuerySet[Appointment]:
    queryset = (
        Appointment.objects.filter(organization=organization)
        .select_related(
            "organization",
            "branch",
            "customer",
            "provider",
            "provider__user",
            "offering",
            "payment",
        )
        .order_by("-start_at")
    )


    if not include_cancelled:
        queryset = queryset.exclude(
            status__in=[
                "cancelled_by_customer",
                "cancelled_by_provider",
            ]
        )


    return queryset
