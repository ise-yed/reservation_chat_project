from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.organizations.permissions import can_manage_organization


def can_view_appointment(user, appointment) -> bool:
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if appointment.customer_id == user.id:
        return True

    if appointment.provider.user_id == user.id:
        return True

    return can_manage_organization(user, appointment.organization)


def can_manage_appointment(user, appointment) -> bool:
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if appointment.provider.user_id == user.id:
        return True

    return can_manage_organization(user, appointment.organization)


def can_cancel_appointment(user, appointment) -> bool:
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if appointment.customer_id == user.id:
        return True

    if appointment.provider.user_id == user.id:
        return True

    return can_manage_organization(user, appointment.organization)


class CanViewOrManageAppointment(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return can_view_appointment(request.user, obj)

        return can_manage_appointment(request.user, obj)
