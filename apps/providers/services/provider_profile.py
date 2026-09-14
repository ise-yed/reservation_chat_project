"""
Service layer for ProviderProfile model operations.
"""

from django.db import IntegrityError, transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.providers.models import ProviderProfile
from apps.providers.permissions import (
    can_create_provider_profile,
    can_manage_provider_organization_fields,
    can_manage_provider_profile,
)
from apps.providers.services.helpers import (
    get_branch_or_raise,
    get_organization_or_raise,
    get_user_or_raise,
    validate_provider_user,
    validate_slot_duration,
)


@transaction.atomic
def create_provider_profile(
    *,
    actor,
    user_id,
    organization_id,
    branch_id=None,
    title: str = "",
    specialty: str = "",
    bio: str = "",
    default_slot_duration_minutes: int = 30,
    is_active: bool = True,
) -> ProviderProfile:
    """Create a new provider profile for a user in an organization."""
    organization = get_organization_or_raise(organization_id=organization_id)

    if not can_create_provider_profile(actor, organization):
        raise PermissionDenied(
            "You are not allowed to create provider profile for this organization."
        )

    if not organization.is_active:
        raise ValidationError(
            {"organization_id": ["Cannot create provider for inactive organization."]}
        )

    user = get_user_or_raise(user_id=user_id)
    validate_provider_user(user)
    validate_slot_duration(default_slot_duration_minutes)

    branch = None
    if branch_id:
        branch = get_branch_or_raise(
            branch_id=branch_id,
            organization=organization,
        )

        if not branch.is_active:
            raise ValidationError({"branch_id": ["Cannot assign provider to inactive branch."]})

    duplicate_exists = ProviderProfile.objects.filter(
        user=user,
        organization=organization,
    ).exists()

    if duplicate_exists:
        raise ValidationError(
            {"user_id": ["This user already has provider profile in this organization."]}
        )

    try:
        return ProviderProfile.objects.create(
            user=user,
            organization=organization,
            branch=branch,
            title=title.strip(),
            specialty=specialty.strip(),
            bio=bio,
            default_slot_duration_minutes=default_slot_duration_minutes,
            is_active=is_active,
        )
    except IntegrityError as exc:
        raise ValidationError(
            {"user_id": ["This user already has provider profile in this organization."]}
        ) from exc


@transaction.atomic
def update_provider_profile(
    *,
    provider_profile: ProviderProfile,
    actor,
    **data,
) -> ProviderProfile:
    """Update a provider profile with partial data support."""
    if not can_manage_provider_profile(actor, provider_profile):
        raise PermissionDenied("You are not allowed to manage this provider profile.")

    organization_fields = {"branch_id", "is_active"}
    wants_to_update_organization_fields = any(field in data for field in organization_fields)

    if wants_to_update_organization_fields and not can_manage_provider_organization_fields(
        actor,
        provider_profile,
    ):
        raise PermissionDenied("You are not allowed to update organization-level provider fields.")

    if "default_slot_duration_minutes" in data:
        validate_slot_duration(data["default_slot_duration_minutes"])

    branch_marker = object()
    branch_id = data.pop("branch_id", branch_marker)

    if branch_id is not branch_marker:
        if branch_id is None:
            provider_profile.branch = None
        else:
            branch = get_branch_or_raise(
                branch_id=branch_id,
                organization=provider_profile.organization,
            )

            if not branch.is_active:
                raise ValidationError({"branch_id": ["Cannot assign provider to inactive branch."]})

            provider_profile.branch = branch

    allowed_fields = {
        "title",
        "specialty",
        "bio",
        "default_slot_duration_minutes",
        "is_active",
    }

    update_fields = []

    if branch_id is not branch_marker:
        update_fields.append("branch")

    for field in allowed_fields:
        if field in data:
            value = data[field]
            if isinstance(value, str):
                value = value.strip()

            setattr(provider_profile, field, value)
            update_fields.append(field)

    if update_fields:
        update_fields.append("updated_at")
        provider_profile.save(update_fields=update_fields)

    return provider_profile
