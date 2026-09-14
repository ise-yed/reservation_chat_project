"""
Tests for organization serializers
"""

import pytest
from django.contrib.auth import get_user_model

from apps.organizations.api.v1.serializers import (
    OrganizationCreateSerializer,
    OrganizationReadSerializer,
    OrganizationUpdateSerializer,
)
from apps.organizations.tests.factories import OrganizationFactory
from apps.users.enums import UserRoles
from apps.users.tests.factories import UserFactory

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestOrganizationReadSerializer:
    """Tests for OrganizationReadSerializer"""

    def test_serializer_contains_all_fields(self):
        """Test that serializer returns all expected fields"""
        user = UserFactory(role=UserRoles.PROVIDER)
        organization = OrganizationFactory(owner=user)

        serializer = OrganizationReadSerializer(organization)
        data = serializer.data

        expected_fields = {
            "id",
            "owner",
            "name",
            "slug",
            "description",
            "phone_number",
            "email",
            "website",
            "timezone",
            "is_active",
            "active_branches_count",
            "created_at",
            "updated_at",
        }
        assert set(data.keys()) == expected_fields

    def test_owner_is_nested_serializer(self):
        """Test that owner field uses nested UserReadSerializer"""
        # Create user with required fields (your User model may not have username)
        user = UserFactory(role=UserRoles.PROVIDER)
        organization = OrganizationFactory(owner=user)

        serializer = OrganizationReadSerializer(organization)
        data = serializer.data

        assert "owner" in data
        assert data["owner"]["id"] == str(user.id)

    def test_active_branches_count_without_annotation(self):
        """Test that active_branches_count returns 0 when no branches exist"""
        organization = OrganizationFactory()

        serializer = OrganizationReadSerializer(organization)
        data = serializer.data

        assert "active_branches_count" in data
        assert data["active_branches_count"] == 0

    def test_read_only_fields_are_respected(self):
        """Test that all fields are read-only in read serializer"""
        serializer = OrganizationReadSerializer()

        for field in serializer.Meta.fields:
            assert field in serializer.Meta.read_only_fields


class TestOrganizationCreateSerializer:
    """Tests for OrganizationCreateSerializer"""

    def test_valid_data_creates_organization(self):
        """Test that valid data passes validation"""
        data = {
            "name": "New Clinic",
            "slug": "new-clinic",
            "description": "A new clinic",
            "phone_number": "02112345678",
            "email": "clinic@example.com",
            "website": "https://clinic.com",
            "timezone": "Asia/Tehran",
            "is_active": True,
        }

        serializer = OrganizationCreateSerializer(data=data)
        assert serializer.is_valid() is True
        assert serializer.validated_data["name"] == "New Clinic"

    def test_slug_is_optional(self):
        """Test that slug field is optional"""
        data = {
            "name": "Clinic Without Slug",
        }

        serializer = OrganizationCreateSerializer(data=data)
        assert serializer.is_valid() is True

    def test_name_is_required(self):
        """Test that name field is required"""
        data = {
            "slug": "test",
        }

        serializer = OrganizationCreateSerializer(data=data)
        assert serializer.is_valid() is False
        assert "name" in serializer.errors

    def test_name_cannot_be_empty_string(self):
        """Test that name cannot be empty or whitespace"""
        data = {
            "name": "   ",
        }

        serializer = OrganizationCreateSerializer(data=data)
        assert serializer.is_valid() is False
        error_msg = str(serializer.errors["name"][0])
        assert "Organization name is required" in error_msg or "blank" in error_msg

    def test_name_is_stripped(self):
        """Test that name is stripped of whitespace"""
        data = {
            "name": "  Test Clinic  ",
        }

        serializer = OrganizationCreateSerializer(data=data)
        assert serializer.is_valid() is True
        assert serializer.validated_data["name"] == "Test Clinic"

    def test_slug_is_optional_and_can_be_blank(self):
        """Test that slug can be blank"""
        data = {
            "name": "Clinic",
            "slug": "",
        }

        serializer = OrganizationCreateSerializer(data=data)
        assert serializer.is_valid() is True


class TestOrganizationUpdateSerializer:
    """Tests for OrganizationUpdateSerializer"""

    def test_all_fields_are_optional(self):
        """Test that all fields are optional in update serializer"""
        data = {
            "name": "Updated Clinic",
        }

        serializer = OrganizationUpdateSerializer(data=data)
        assert serializer.is_valid() is True
        assert serializer.validated_data["name"] == "Updated Clinic"

    def test_partial_update_without_all_fields(self):
        """Test that partial update works without all fields"""
        data = {
            "is_active": False,
        }

        serializer = OrganizationUpdateSerializer(data=data)
        assert serializer.is_valid() is True
        assert serializer.validated_data["is_active"] is False

    def test_name_cannot_be_empty_when_provided(self):
        """Test that name cannot be whitespace when provided"""
        data = {
            "name": "   ",
        }

        serializer = OrganizationUpdateSerializer(data=data)
        assert serializer.is_valid() is False

    def test_name_not_provided_is_ignored(self):
        """Test that when name is not provided, it's not in validated_data"""
        data = {
            "description": "New description",
        }

        serializer = OrganizationUpdateSerializer(data=data)
        assert serializer.is_valid() is True
        assert "name" not in serializer.validated_data

    def test_empty_string_name_raises_error(self):
        """Test that empty string name raises validation error"""
        data = {
            "name": "",
        }

        serializer = OrganizationUpdateSerializer(data=data)
        assert serializer.is_valid() is False
        assert "Organization name cannot be empty" in str(serializer.errors["name"])

    def test_whitespace_only_name_raises_error(self):
        """Test that whitespace-only name raises validation error"""
        data = {
            "name": "   ",
        }

        serializer = OrganizationUpdateSerializer(data=data)
        assert serializer.is_valid() is False
        assert "Organization name cannot be empty" in str(serializer.errors["name"])

    def test_valid_slug_is_accepted(self):
        """Test that valid slug passes validation"""
        data = {
            "slug": "valid-slug-123",
        }

        serializer = OrganizationUpdateSerializer(data=data)
        assert serializer.is_valid() is True
        assert serializer.validated_data["slug"] == "valid-slug-123"
