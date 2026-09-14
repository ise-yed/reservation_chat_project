from decimal import Decimal

from rest_framework.exceptions import ValidationError


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
