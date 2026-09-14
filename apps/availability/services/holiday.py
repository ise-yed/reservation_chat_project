from django.db import IntegrityError, transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.availability.models import Holiday
from apps.availability.permissions import can_manage_organization_holidays
from apps.availability.services.helpers import get_organization_or_raise


@transaction.atomic
def create_holiday(
    *,
    actor,
    organization_id,
    date,
    title: str,
    is_active: bool = True,
) -> Holiday:
    """Create a new holiday."""
    organization = get_organization_or_raise(organization_id=organization_id)

    if not can_manage_organization_holidays(actor, organization):
        raise PermissionDenied("You are not allowed to manage organization holidays.")

    if not organization.is_active:
        raise ValidationError(
            {"organization_id": ["Cannot create holiday for inactive organization."]}
        )

    duplicate_exists = Holiday.objects.filter(
        organization=organization,
        date=date,
    ).exists()

    if duplicate_exists:
        raise ValidationError({"date": ["This organization already has a holiday on this date."]})

    try:
        return Holiday.objects.create(
            organization=organization,
            date=date,
            title=title.strip(),
            is_active=is_active,
        )
    except IntegrityError as exc:
        raise ValidationError(
            {"date": ["This organization already has a holiday on this date."]}
        ) from exc


@transaction.atomic
def update_holiday(
    *,
    holiday: Holiday,
    actor,
    **data,
) -> Holiday:
    """Update an existing holiday."""
    if not can_manage_organization_holidays(actor, holiday.organization):
        raise PermissionDenied("You are not allowed to manage organization holidays.")

    if "date" in data:
        duplicate_exists = (
            Holiday.objects.filter(
                organization=holiday.organization,
                date=data["date"],
            )
            .exclude(id=holiday.id)
            .exists()
        )

        if duplicate_exists:
            raise ValidationError(
                {"date": ["This organization already has a holiday on this date."]}
            )

    allowed_fields = {
        "date",
        "title",
        "is_active",
    }

    update_fields = []

    for field in allowed_fields:
        if field in data:
            value = data[field]
            if isinstance(value, str):
                value = value.strip()

            setattr(holiday, field, value)
            update_fields.append(field)

    if update_fields:
        update_fields.append("updated_at")
        holiday.save(update_fields=update_fields)

    return holiday
