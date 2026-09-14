"""
Database selectors for Organization and Branch models.
"""

from django.db.models import Count, Q, QuerySet

from apps.organizations.models import Branch, Organization


def get_active_organizations() -> QuerySet[Organization]:
    """Return all active organizations with owner and active branches count."""
    return (
        Organization.objects.filter(is_active=True)
        .select_related("owner")
        .annotate(
            active_branches_count=Count(
                "branches",
                filter=Q(branches__is_active=True),
            )
        )
        .order_by("-created_at")
    )


def get_user_owned_organizations(*, user) -> QuerySet[Organization]:
    """Return all organizations owned by the given user."""
    return (
        Organization.objects.filter(owner=user)
        .select_related("owner")
        .annotate(
            active_branches_count=Count(
                "branches",
                filter=Q(branches__is_active=True),
            )
        )
        .order_by("-created_at")
    )


def get_organization_by_id(*, organization_id) -> Organization:
    """Return an organization by ID with owner prefetched."""
    return Organization.objects.select_related("owner").get(id=organization_id)


def get_organization_by_slug(*, slug: str) -> Organization:
    """Return an organization by slug with owner prefetched."""
    return Organization.objects.select_related("owner").get(slug=slug)


def get_organization_branches(
    *,
    organization: Organization,
    include_inactive: bool = False,
) -> QuerySet[Branch]:
    """Return branches for an organization, optionally including inactive ones."""
    queryset = Branch.objects.filter(organization=organization)

    if not include_inactive:
        queryset = queryset.filter(is_active=True)

    return queryset.order_by("name")


def get_branch_by_id(*, branch_id) -> Branch:
    """Return a branch by ID with organization and owner prefetched."""
    return Branch.objects.select_related("organization", "organization__owner").get(id=branch_id)
