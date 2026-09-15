import pytest
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.organizations.tests.factories import BranchFactory, OrganizationFactory
from apps.providers.services import (
    create_provider_profile,
    update_provider_profile,
)
from apps.providers.tests.factories import ProviderProfileFactory
from apps.users.enums import UserRoles
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_organization_owner_can_create_provider_profile():
    owner = UserFactory(role=UserRoles.PROVIDER)
    provider_user = UserFactory(role=UserRoles.PROVIDER)
    organization = OrganizationFactory(owner=owner)
    branch = BranchFactory(organization=organization)

    provider_profile = create_provider_profile(
        actor=owner,
        user_id=provider_user.id,
        organization_id=organization.id,
        branch_id=branch.id,
        title="Dr.",
        specialty_ids=[],
        default_slot_duration_minutes=30,
    )

    assert provider_profile.user == provider_user
    assert provider_profile.organization == organization
    assert provider_profile.branch == branch
    # اصلاح شد: به جای تست رشته متنی، تعداد تخصص‌ها را بررسی می‌کنیم
    assert provider_profile.specialties.count() == 0


def test_non_owner_cannot_create_provider_profile():
    owner = UserFactory(role=UserRoles.PROVIDER)
    other_user = UserFactory(role=UserRoles.PROVIDER)
    provider_user = UserFactory(role=UserRoles.PROVIDER)
    organization = OrganizationFactory(owner=owner)

    with pytest.raises(PermissionDenied):
        create_provider_profile(
            actor=other_user,
            user_id=provider_user.id,
            organization_id=organization.id,
        )


def test_customer_user_cannot_be_provider():
    owner = UserFactory(role=UserRoles.PROVIDER)
    customer = UserFactory(role=UserRoles.CUSTOMER)
    organization = OrganizationFactory(owner=owner)

    with pytest.raises(ValidationError):
        create_provider_profile(
            actor=owner,
            user_id=customer.id,
            organization_id=organization.id,
        )


def test_duplicate_provider_profile_in_same_organization_is_not_allowed():
    owner = UserFactory(role=UserRoles.PROVIDER)
    provider_user = UserFactory(role=UserRoles.PROVIDER)
    organization = OrganizationFactory(owner=owner)

    create_provider_profile(
        actor=owner,
        user_id=provider_user.id,
        organization_id=organization.id,
    )

    with pytest.raises(ValidationError):
        create_provider_profile(
            actor=owner,
            user_id=provider_user.id,
            organization_id=organization.id,
        )


def test_provider_can_update_own_public_profile_fields():
    provider_user = UserFactory(role=UserRoles.PROVIDER)
    organization = OrganizationFactory()
    provider_profile = ProviderProfileFactory(
        user=provider_user,
        organization=organization,
        title="Old Title",
    )

    updated = update_provider_profile(
        provider_profile=provider_profile,
        actor=provider_user,
        title="New Title",
        specialty_ids=[],  # اصلاح شد
    )

    assert updated.title == "New Title"
    assert updated.specialties.count() == 0  # اصلاح شد


def test_provider_cannot_update_own_is_active_field():
    provider_user = UserFactory(role=UserRoles.PROVIDER)
    organization = OrganizationFactory()
    provider_profile = ProviderProfileFactory(
        user=provider_user,
        organization=organization,
        is_active=True,
    )

    with pytest.raises(PermissionDenied):
        update_provider_profile(
            provider_profile=provider_profile,
            actor=provider_user,
            is_active=False,
        )


def test_organization_owner_can_update_provider_branch_and_active_status():
    owner = UserFactory(role=UserRoles.PROVIDER)
    provider_user = UserFactory(role=UserRoles.PROVIDER)
    organization = OrganizationFactory(owner=owner)
    old_branch = BranchFactory(organization=organization)
    new_branch = BranchFactory(organization=organization)

    provider_profile = ProviderProfileFactory(
        user=provider_user,
        organization=organization,
        branch=old_branch,
        is_active=True,
    )

    updated = update_provider_profile(
        provider_profile=provider_profile,
        actor=owner,
        branch_id=new_branch.id,
        is_active=False,
    )

    assert updated.branch == new_branch
    assert updated.is_active is False


def test_non_manager_cannot_update_provider_profile():
    owner = UserFactory(role=UserRoles.PROVIDER)
    other_user = UserFactory(role=UserRoles.PROVIDER)
    provider_user = UserFactory(role=UserRoles.PROVIDER)
    organization = OrganizationFactory(owner=owner)

    provider_profile = ProviderProfileFactory(
        user=provider_user,
        organization=organization,
    )

    with pytest.raises(PermissionDenied):
        update_provider_profile(
            provider_profile=provider_profile,
            actor=other_user,
            title="Invalid",
        )
