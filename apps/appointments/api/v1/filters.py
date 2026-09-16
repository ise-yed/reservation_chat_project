from django_filters import rest_framework as filters

from apps.appointments.models import Appointment
from apps.offerings.enums import VisitMode


class AppointmentFilter(filters.FilterSet):
    """Filter for appointments."""

    visit_mode = filters.ChoiceFilter(choices=VisitMode.choices)
    status = filters.CharFilter(field_name="status")

    class Meta:
        model = Appointment
        fields = [
            "visit_mode",
            "status",
            "organization",
            "provider",
        ]