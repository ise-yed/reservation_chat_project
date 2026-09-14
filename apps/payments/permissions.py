from apps.organizations.permissions import can_manage_organization


def can_view_payment(user, payment) -> bool:
    """Check if user can view a payment."""
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if payment.payer_id == user.id:
        return True

    if payment.appointment.customer_id == user.id:
        return True

    if payment.appointment.provider.user_id == user.id:
        return True

    return can_manage_organization(user, payment.organization)


def can_manage_payment(user, payment) -> bool:
    """Check if user can manage a payment."""
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if payment.appointment.provider.user_id == user.id:
        return True

    return can_manage_organization(user, payment.organization)


def can_create_payment_for_appointment(user, appointment) -> bool:
    """Check if user can create a payment for an appointment."""
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return appointment.customer_id == user.id
