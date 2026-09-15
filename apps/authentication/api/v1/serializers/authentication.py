from django.contrib.auth import authenticate, password_validation
from rest_framework import serializers

from apps.users.api.v1.serializers.users import UserReadSerializer
from apps.users.enums import UserRoles
from apps.users.models import User


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Validates email uniqueness, password strength, and password confirmation.
    """

    password = serializers.CharField(
        write_only=True, min_length=8, style={"input_type": "password"}
    )
    password_confirm = serializers.CharField(
        write_only=True, min_length=8, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "password",
            "password_confirm",
        )

    def validate_role(self, value):
        """Ensure role is always customer for public registration."""
        if value != UserRoles.CUSTOMER:
            raise serializers.ValidationError("Public registration is only allowed for patients (customers).")
        return value

    def validate_email(self, value):
        """Normalize email and ensure it's unique."""
        value = value.lower().strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        """Validate password match and password strength."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})

        temp_user = User(
            email=attrs.get("email"),
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
        )
        password_validation.validate_password(attrs["password"], temp_user)
        return attrs


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.

    Authenticates user with email and password.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        """Authenticate user and check account status."""
        email = attrs.get("email", "").lower().strip()
        password = attrs.get("password")

        user = authenticate(
            request=self.context.get("request"),
            email=email,
            password=password,
        )

        if not user:
            raise serializers.ValidationError({"non_field_errors": ["Invalid email or password."]})

        if not user.is_active:
            raise serializers.ValidationError({"non_field_errors": ["This account is inactive."]})

        attrs["user"] = user
        return attrs


class TokenPairSerializer(serializers.Serializer):
    """Serializer for JWT token pair response."""

    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user = UserReadSerializer(read_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing authenticated user's password.

    Validates current password, new password match, and password strength.
    """

    current_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(
        write_only=True, min_length=8, style={"input_type": "password"}
    )
    new_password_confirm = serializers.CharField(
        write_only=True, min_length=8, style={"input_type": "password"}
    )

    def validate(self, attrs):
        """Validate current password, new password match, and strength."""
        user = self.context["request"].user

        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError(
                {"current_password": ["Current password is incorrect."]}
            )

        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": ["Passwords do not match."]})

        password_validation.validate_password(attrs["new_password"], user)
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting password reset email."""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming password reset.

    Validates token, uid, and new password match.
    """

    token = serializers.CharField()
    uid = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True, min_length=8, style={"input_type": "password"}
    )
    new_password_confirm = serializers.CharField(
        write_only=True, min_length=8, style={"input_type": "password"}
    )

    def validate(self, attrs):
        """Ensure new passwords match."""
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": ["Passwords do not match."]})
        return attrs
