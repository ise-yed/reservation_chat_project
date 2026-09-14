"""
Service layer for Organization model operations.

Contains business logic for creating and updating organizations.
"""

from django.db import transaction
from django.utils.text import slugify
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.organizations.models import Organization
from apps.organizations.permissions import (
    can_create_organization,
    can_manage_organization,
)


def _generate_unique_slug(*, name: str, slug: str | None = None) -> str:
    """Generate a unique slug for an organization."""
    base_slug = slugify(slug or name, allow_unicode=True).strip("-")

    if not base_slug:
        base_slug = "organization"

    final_slug = base_slug
    counter = 1

    while Organization.objects.filter(slug=final_slug).exists():
        counter += 1
        final_slug = f"{base_slug}-{counter}"

    return final_slug


def _ensure_can_create_organization(user) -> None:
    """Raise PermissionDenied if user cannot create an organization."""
    if not can_create_organization(user):
        raise PermissionDenied("You are not allowed to create an organization.")


def _ensure_can_manage_organization(user, organization: Organization) -> None:
    """Raise PermissionDenied if user cannot manage the organization."""
    if not can_manage_organization(user, organization):
        raise PermissionDenied("You are not allowed to manage this organization.")


@transaction.atomic
def create_organization(
    *,
    owner,
    name: str,
    slug: str | None = None,
    description: str = "",
    phone_number: str = "",
    email: str = "",
    website: str = "",
    timezone: str = "Asia/Tehran",
    is_active: bool = True,
) -> Organization:
    """Create a new organization with a unique slug."""
    _ensure_can_create_organization(owner)
    final_slug = _generate_unique_slug(name=name, slug=slug)

    return Organization.objects.create(
        owner=owner,
        name=name.strip(),
        slug=final_slug,
        description=description,
        phone_number=phone_number,
        email=email,
        website=website,
        timezone=timezone,
        is_active=is_active,
    )


@transaction.atomic
def update_organization(
    *,
    organization: Organization,
    actor,
    **data,
) -> Organization:
    """Update an organization with partial data and unique slug validation."""
    _ensure_can_manage_organization(actor, organization)

    allowed_fields = {
        "name",
        "description",
        "phone_number",
        "email",
        "website",
        "timezone",
        "is_active",
    }

    update_fields = []

    for field in allowed_fields:
        if field in data:
            setattr(organization, field, data[field])
            update_fields.append(field)

    if "slug" in data and data["slug"]:
        new_slug = slugify(data["slug"], allow_unicode=True).strip("-")
        if not new_slug:
            raise ValidationError({"slug": ["Invalid slug."]})

        slug_exists = (
            Organization.objects.filter(slug=new_slug).exclude(id=organization.id).exists()
        )
        if slug_exists:
            raise ValidationError({"slug": ["This slug is already in use."]})

        organization.slug = new_slug
        update_fields.append("slug")

    if update_fields:
        update_fields.append("updated_at")
        organization.save(update_fields=update_fields)

    return organization
