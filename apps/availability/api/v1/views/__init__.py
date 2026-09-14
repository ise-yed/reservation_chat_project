from apps.availability.api.v1.views.holidays import (
    HolidayDetailView,
    HolidayListCreateView,
    OrganizationHolidayListView,
)
from apps.availability.api.v1.views.slots import AvailableSlotView
from apps.availability.api.v1.views.time_offs import (
    ProviderTimeOffListView,
    TimeOffDetailView,
    TimeOffListCreateView,
)
from apps.availability.api.v1.views.working_hours import (
    ProviderWorkingHourListView,
    WorkingHourDetailView,
    WorkingHourListCreateView,
)

__all__ = [
    "WorkingHourListCreateView",
    "WorkingHourDetailView",
    "ProviderWorkingHourListView",
    "TimeOffListCreateView",
    "TimeOffDetailView",
    "ProviderTimeOffListView",
    "HolidayListCreateView",
    "HolidayDetailView",
    "OrganizationHolidayListView",
    "AvailableSlotView",
]
