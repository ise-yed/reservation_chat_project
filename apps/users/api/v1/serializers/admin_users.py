"""
Admin serializers for User management.
Only accessible by staff / org_admin / super_admin.
"""
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.users.enums import UserRoles
from apps.users.models import User


class AdminUserReadSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone_number",
            "role",
            "is_active",
            "is_verified",
            "is_staff",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.full_name


class AdminUserWriteSerializer(serializers.ModelSerializer):
    """Used for PATCH (partial update) by admin."""

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "is_active",
            "is_verified",
        )


class AdminUserCreateSerializer(serializers.ModelSerializer):
    """Used for POST (create) by admin — sets password via set_password."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "is_active",
            "is_verified",
            "password",
        )

    def validate_role(self, value):
        allowed = {r for r in UserRoles.values}
        if value not in allowed:
            raise serializers.ValidationError(_("Invalid role. Choices: %(choices)s") % {"choices": allowed})
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
