"""
Helper functions and Validation utilities for provider services.
"""

from rest_framework.exceptions import ValidationError

from apps.organizations.models import Branch, Organization
from apps.users.enums import UserRoles
from apps.users.models import User


def validate_provider_user(user: User) -> None:
    """Validate that user is active and has provider role."""
    if not user.is_active:
        raise ValidationError({"user_id": ["User is not active."]})

    if user.role != UserRoles.PROVIDER:
        raise ValidationError({"user_id": ["Selected user must have provider role."]})


def validate_slot_duration(value: int) -> None:
    """Validate that slot duration is within acceptable range."""
    if value <= 0:
        raise ValidationError(
            {"default_slot_duration_minutes": ["Duration must be greater than zero."]}
        )

    if value > 480:
        raise ValidationError(
            {"default_slot_duration_minutes": ["Duration cannot be more than 480 minutes."]}
        )


def get_user_or_raise(*, user_id) -> User:
    """Retrieve user or raise validation error."""
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist as exc:
        raise ValidationError({"user_id": ["User not found."]}) from exc


def get_organization_or_raise(*, organization_id) -> Organization:
    """Retrieve organization or raise validation error."""
    try:
        return Organization.objects.get(id=organization_id)
    except Organization.DoesNotExist as exc:
        raise ValidationError({"organization_id": ["Organization not found."]}) from exc


def get_branch_or_raise(*, branch_id, organization: Organization) -> Branch:
    """Retrieve branch belonging to organization or raise validation error."""
    try:
        return Branch.objects.get(id=branch_id, organization=organization)
    except Branch.DoesNotExist as exc:
        raise ValidationError({"branch_id": ["Branch not found for this organization."]}) from exc
