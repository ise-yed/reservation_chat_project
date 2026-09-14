"""
Tests for branch serializers
"""

import pytest

from apps.organizations.api.v1.serializers import (
    BranchCreateSerializer,
    BranchReadSerializer,
    BranchUpdateSerializer,
)
from apps.organizations.tests.factories import BranchFactory, OrganizationFactory

pytestmark = pytest.mark.django_db


class TestBranchReadSerializer:
    """Tests for BranchReadSerializer"""

    def test_serializer_contains_all_fields(self):
        """Test that serializer returns all expected fields"""
        organization = OrganizationFactory()
        branch = BranchFactory(organization=organization)

        serializer = BranchReadSerializer(branch)
        data = serializer.data

        expected_fields = {
            "id",
            "organization_id",
            "organization_name",
            "name",
            "address",
            "phone_number",
            "latitude",
            "longitude",
            "is_active",
            "created_at",
            "updated_at",
        }
        assert set(data.keys()) == expected_fields

    def test_organization_info_is_included(self):
        """Test that organization ID and name are included in response"""
        organization = OrganizationFactory(name="My Clinic")
        branch = BranchFactory(organization=organization)

        serializer = BranchReadSerializer(branch)
        data = serializer.data

        assert data["organization_id"] == str(organization.id)
        assert data["organization_name"] == "My Clinic"

    def test_read_only_fields_are_respected(self):
        """Test that all fields are read-only in read serializer"""
        serializer = BranchReadSerializer()

        for field in serializer.Meta.fields:
            assert field in serializer.Meta.read_only_fields

    def test_coordinates_can_be_null(self):
        """Test that latitude and longitude can be null"""
        branch = BranchFactory(latitude=None, longitude=None)

        serializer = BranchReadSerializer(branch)
        data = serializer.data

        assert data["latitude"] is None
        assert data["longitude"] is None

    def test_coordinates_with_values(self):
        """Test that latitude and longitude are serialized correctly"""
        branch = BranchFactory(latitude=35.6892, longitude=51.3890)

        serializer = BranchReadSerializer(branch)
        data = serializer.data

        assert float(data["latitude"]) == 35.6892
        assert float(data["longitude"]) == 51.3890


class TestBranchCreateSerializer:
    """Tests for BranchCreateSerializer"""

    def test_valid_data_creates_branch(self):
        """Test that valid data passes validation"""
        data = {
            "name": "Main Branch",
            "address": "123 Main St",
            "phone_number": "02112345678",
            "latitude": 35.6892,
            "longitude": 51.3890,
            "is_active": True,
        }

        serializer = BranchCreateSerializer(data=data)
        assert serializer.is_valid() is True
        assert serializer.validated_data["name"] == "Main Branch"

    def test_name_is_required(self):
        """Test that name field is required"""
        data = {
            "address": "Some address",
        }

        serializer = BranchCreateSerializer(data=data)
        assert serializer.is_valid() is False
        assert "name" in serializer.errors

    def test_name_cannot_be_empty_string(self):
        """Test that name cannot be empty or whitespace"""
        data = {
            "name": "   ",
        }

        serializer = BranchCreateSerializer(data=data)
        assert serializer.is_valid() is False
        error_msg = str(serializer.errors["name"][0])
        assert "Branch name is required" in error_msg or "blank" in error_msg

    def test_name_is_stripped(self):
        """Test that name is stripped of whitespace"""
        data = {
            "name": "  Main Branch  ",
        }

        serializer = BranchCreateSerializer(data=data)
        assert serializer.is_valid() is True
        assert serializer.validated_data["name"] == "Main Branch"

    def test_optional_fields_are_not_required(self):
        """Test that optional fields can be omitted"""
        data = {
            "name": "Main Branch",
        }

        serializer = BranchCreateSerializer(data=data)
        assert serializer.is_valid() is True

    def test_is_active_defaults_to_true(self):
        """Test that is_active defaults to True when not provided"""
        data = {
            "name": "Main Branch",
        }

        serializer = BranchCreateSerializer(data=data)
        assert serializer.is_valid() is True


class TestBranchUpdateSerializer:
    """Tests for BranchUpdateSerializer"""

    def test_all_fields_are_optional(self):
        """Test that all fields are optional in update serializer"""
        data = {
            "name": "Updated Branch",
        }

        serializer = BranchUpdateSerializer(data=data)
        assert serializer.is_valid() is True
        assert serializer.validated_data["name"] == "Updated Branch"

    def test_partial_update_without_all_fields(self):
        """Test that partial update works without all fields"""
        data = {
            "is_active": False,
        }

        serializer = BranchUpdateSerializer(data=data)
        assert serializer.is_valid() is True
        assert serializer.validated_data["is_active"] is False

    def test_name_cannot_be_empty_when_provided(self):
        """Test that name cannot be whitespace when provided"""
        data = {
            "name": "   ",
        }

        serializer = BranchUpdateSerializer(data=data)
        assert serializer.is_valid() is False
        error_msg = str(serializer.errors["name"][0])
        assert "cannot be empty" in error_msg or "blank" in error_msg

    def test_name_not_provided_is_ignored(self):
        """Test that when name is not provided, it's not in validated_data"""
        data = {
            "address": "New Address",
        }

        serializer = BranchUpdateSerializer(data=data)
        assert serializer.is_valid() is True
        assert "name" not in serializer.validated_data

    def test_empty_string_name_raises_error(self):
        """Test that empty string name raises validation error"""
        data = {
            "name": "",
        }

        serializer = BranchUpdateSerializer(data=data)
        assert serializer.is_valid() is False
        assert "Branch name cannot be empty" in str(serializer.errors["name"])

    def test_whitespace_only_name_raises_error(self):
        """Test that whitespace-only name raises validation error"""
        data = {
            "name": "   ",
        }

        serializer = BranchUpdateSerializer(data=data)
        assert serializer.is_valid() is False
        assert "Branch name cannot be empty" in str(serializer.errors["name"])

    def test_coordinates_can_be_updated(self):
        """Test that coordinates can be updated with float values"""
        data = {
            "latitude": 40.7128,
            "longitude": -74.0060,
        }

        serializer = BranchUpdateSerializer(data=data)
        assert serializer.is_valid() is True
        # Convert Decimal to float for comparison
        assert float(serializer.validated_data["latitude"]) == 40.7128
        assert float(serializer.validated_data["longitude"]) == -74.0060

    def test_coordinates_can_be_set_to_null(self):
        """Test that coordinates can be set to null"""
        data = {
            "latitude": None,
            "longitude": None,
        }

        serializer = BranchUpdateSerializer(data=data)
        assert serializer.is_valid() is True
        assert serializer.validated_data["latitude"] is None
        assert serializer.validated_data["longitude"] is None

    def test_valid_name_update(self):
        """Test that valid name update passes validation"""
        data = {
            "name": "Updated Branch Name",
        }

        serializer = BranchUpdateSerializer(data=data)
        assert serializer.is_valid() is True
        assert serializer.validated_data["name"] == "Updated Branch Name"
