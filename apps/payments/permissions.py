from apps.organizations.permissions import can_manage_organization


def can_view_payment(user, payment) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    appointment = payment.appointment
    if appointment.customer_id == user.id or appointment.provider.user_id == user.id:
        return True
    return can_manage_organization(user, appointment.organization)


def can_manage_payment(user, payment) -> bool:
    """Provider / organization staff (used to confirm cash or card payment at the clinic)."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    appointment = payment.appointment
    if appointment.provider.user_id == user.id:
        return True
    return can_manage_organization(user, appointment.organization)
