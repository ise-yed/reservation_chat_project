from apps.availability.api.v1.serializers.holidays import (
    HolidayCreateSerializer,
    HolidayReadSerializer,
    HolidayUpdateSerializer,
)
from apps.availability.api.v1.serializers.slots import (
    AvailableSlotQuerySerializer,
    AvailableSlotSerializer,
)
from apps.availability.api.v1.serializers.time_off import (
    TimeOffCreateSerializer,
    TimeOffReadSerializer,
    TimeOffUpdateSerializer,
)
from apps.availability.api.v1.serializers.working_hour import (
    WorkingHourCreateSerializer,
    WorkingHourReadSerializer,
    WorkingHourUpdateSerializer,
)

__all__ = [
    "WorkingHourCreateSerializer",
    "WorkingHourReadSerializer",
    "WorkingHourUpdateSerializer",
    "TimeOffCreateSerializer",
    "TimeOffReadSerializer",
    "TimeOffUpdateSerializer",
    "HolidayCreateSerializer",
    "HolidayReadSerializer",
    "HolidayUpdateSerializer",
    "AvailableSlotQuerySerializer",
    "AvailableSlotSerializer",
]
