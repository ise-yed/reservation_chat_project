"""
Service layer for Branch model operations.

Contains business logic for creating and updating branches.
"""

from django.db import IntegrityError, transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.organizations.models import Branch, Organization
from apps.organizations.permissions import can_manage_organization


def _ensure_can_manage_organization(user, organization: Organization) -> None:
    """Raise PermissionDenied if user cannot manage the organization."""
    if not can_manage_organization(user, organization):
        raise PermissionDenied("You are not allowed to manage this organization.")


@transaction.atomic
def create_branch(
    *,
    organization: Organization,
    actor,
    name: str,
    address: str = "",
    phone_number: str = "",
    latitude=None,
    longitude=None,
    is_active: bool = True,
) -> Branch:
    """Create a new branch under an organization with duplicate name validation."""
    _ensure_can_manage_organization(actor, organization)

    if not organization.is_active:
        raise ValidationError(
            {"organization": ["Cannot create a branch for an inactive organization."]}
        )

    duplicate_exists = Branch.objects.filter(
        organization=organization,
        name__iexact=name.strip(),
    ).exists()

    if duplicate_exists:
        raise ValidationError(
            {"name": ["A branch with this name already exists in this organization."]}
        )

    try:
        return Branch.objects.create(
            organization=organization,
            name=name.strip(),
            address=address,
            phone_number=phone_number,
            latitude=latitude,
            longitude=longitude,
            is_active=is_active,
        )
    except IntegrityError as exc:
        raise ValidationError(
            {"name": ["A branch with this name already exists in this organization."]}
        ) from exc


@transaction.atomic
def update_branch(
    *,
    branch: Branch,
    actor,
    **data,
) -> Branch:
    """Update a branch with partial data and duplicate name validation."""
    _ensure_can_manage_organization(actor, branch.organization)

    if "name" in data:
        duplicate_exists = (
            Branch.objects.filter(
                organization=branch.organization,
                name__iexact=data["name"].strip(),
            )
            .exclude(id=branch.id)
            .exists()
        )

        if duplicate_exists:
            raise ValidationError(
                {"name": ["A branch with this name already exists in this organization."]}
            )

    allowed_fields = {
        "name",
        "address",
        "phone_number",
        "latitude",
        "longitude",
        "is_active",
    }

    update_fields = []

    for field in allowed_fields:
        if field in data:
            value = data[field]
            if isinstance(value, str):
                value = value.strip()
            setattr(branch, field, value)
            update_fields.append(field)

    if update_fields:
        update_fields.append("updated_at")
        branch.save(update_fields=update_fields)

    return branch
