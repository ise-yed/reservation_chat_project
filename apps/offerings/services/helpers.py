from decimal import Decimal

from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.organizations.models import Organization
from apps.organizations.permissions import can_manage_organization
from apps.providers.models import ProviderProfile


def get_organization_or_raise(*, organization_id) -> Organization:
    """Get organization by ID or raise validation error."""
    try:
        return Organization.objects.get(id=organization_id)
    except Organization.DoesNotExist as exc:
        raise ValidationError({"organization_id": ["Organization not found."]}) from exc


def get_provider_or_raise(*, provider_id) -> ProviderProfile:
    """Get provider by ID or raise validation error."""
    try:
        return ProviderProfile.objects.select_related("organization", "user", "branch").get(
            id=provider_id
        )
    except ProviderProfile.DoesNotExist as exc:
        raise ValidationError({"provider_id": ["Provider not found."]}) from exc


def ensure_can_manage_organization(actor, organization) -> None:
    """Ensure user can manage the organization."""
    if not can_manage_organization(actor, organization):
        raise PermissionDenied("You are not allowed to manage offerings for this organization.")


def validate_provider_belongs_to_organization(*, provider, organization) -> None:
    """Validate provider belongs to the organization."""
    if provider.organization_id != organization.id:
        raise ValidationError({"provider_id": ["Provider does not belong to this organization."]})


def validate_duration_minutes(value: int) -> None:
    """Validate duration minutes is between 1 and 480."""
    if value <= 0:
        raise ValidationError({"duration_minutes": ["Duration must be greater than zero."]})

    if value > 480:
        raise ValidationError({"duration_minutes": ["Duration cannot be more than 480 minutes."]})


def validate_buffer_minutes(*, field_name: str, value: int) -> None:
    """Validate buffer minutes is between 0 and 240."""
    if value < 0:
        raise ValidationError({field_name: ["Buffer cannot be negative."]})

    if value > 240:
        raise ValidationError({field_name: ["Buffer cannot be more than 240 minutes."]})


def validate_price(value) -> None:
    """Validate price is not negative."""
    price = Decimal(value)

    if price < 0:
        raise ValidationError({"price": ["Price cannot be negative."]})


def validate_offering_payload(
    *,
    duration_minutes: int | None = None,
    buffer_before_minutes: int | None = None,
    buffer_after_minutes: int | None = None,
    price=None,
) -> None:
    """Validate offering payload fields."""

    if duration_minutes is not None:
        validate_duration_minutes(duration_minutes)

    if buffer_before_minutes is not None:
        validate_buffer_minutes(
            field_name="buffer_before_minutes",
            value=buffer_before_minutes,
        )

    if buffer_after_minutes is not None:
        validate_buffer_minutes(
            field_name="buffer_after_minutes",
            value=buffer_after_minutes,
        )

    if price is not None:
        validate_price(price)
