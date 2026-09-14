from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from apps.offerings.models import Offering
from apps.offerings.services.helpers import (
    ensure_can_manage_organization,
    get_organization_or_raise,
    get_provider_or_raise,
    validate_offering_payload,
    validate_provider_belongs_to_organization,
)


@transaction.atomic
def create_offering(
    *,
    actor,
    organization_id,
    provider_id,
    title: str,
    description: str = "",
    duration_minutes: int = 30,
    buffer_before_minutes: int = 0,
    buffer_after_minutes: int = 0,
    price=0,
    requires_approval: bool = False,
    is_active: bool = True,
) -> Offering:
    """Create a new offering."""
    organization = get_organization_or_raise(organization_id=organization_id)
    ensure_can_manage_organization(actor, organization)

    if not organization.is_active:
        raise ValidationError(
            {"organization_id": ["Cannot create offering for inactive organization."]}
        )

    provider = get_provider_or_raise(provider_id=provider_id)
    validate_provider_belongs_to_organization(
        provider=provider,
        organization=organization,
    )

    if not provider.is_active:
        raise ValidationError({"provider_id": ["Cannot create offering for inactive provider."]})

    validate_offering_payload(
        duration_minutes=duration_minutes,
        buffer_before_minutes=buffer_before_minutes,
        buffer_after_minutes=buffer_after_minutes,
        price=price,
    )

    clean_title = title.strip()

    duplicate_exists = Offering.objects.filter(
        provider=provider,
        title__iexact=clean_title,
    ).exists()

    if duplicate_exists:
        raise ValidationError({"title": ["This provider already has an offering with this title."]})

    try:
        return Offering.objects.create(
            organization=organization,
            provider=provider,
            title=clean_title,
            description=description,
            duration_minutes=duration_minutes,
            buffer_before_minutes=buffer_before_minutes,
            buffer_after_minutes=buffer_after_minutes,
            price=price,
            requires_approval=requires_approval,
            is_active=is_active,
        )
    except IntegrityError as exc:
        raise ValidationError(
            {"title": ["This provider already has an offering with this title."]}
        ) from exc


@transaction.atomic
def update_offering(
    *,
    offering: Offering,
    actor,
    **data,
) -> Offering:
    """Update an existing offering."""
    ensure_can_manage_organization(actor, offering.organization)

    validate_offering_payload(
        duration_minutes=data.get("duration_minutes"),
        buffer_before_minutes=data.get("buffer_before_minutes"),
        buffer_after_minutes=data.get("buffer_after_minutes"),
        price=data.get("price"),
    )

    if "title" in data:
        clean_title = data["title"].strip()

        duplicate_exists = (
            Offering.objects.filter(provider=offering.provider, title__iexact=clean_title)
            .exclude(id=offering.id)
            .exists()
        )

        if duplicate_exists:
            raise ValidationError(
                {"title": ["This provider already has an offering with this title."]}
            )

        data["title"] = clean_title

    allowed_fields = {
        "title",
        "description",
        "duration_minutes",
        "buffer_before_minutes",
        "buffer_after_minutes",
        "price",
        "requires_approval",
        "is_active",
    }

    update_fields = []

    for field in allowed_fields:
        if field in data:
            value = data[field]
            if isinstance(value, str):
                value = value.strip()

            setattr(offering, field, value)
            update_fields.append(field)

    if update_fields:
        update_fields.append("updated_at")
        offering.save(update_fields=update_fields)

    return offering
