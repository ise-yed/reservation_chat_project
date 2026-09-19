from django.contrib.auth import authenticate, password_validation
from rest_framework import serializers

from apps.users.api.v1.serializers.users import UserReadSerializer
from apps.users.models import User


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "phone_number", "password", "password_confirm")

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
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
    """Serializer for user login."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        email = attrs.get("email", "").lower().strip()
        password = attrs.get("password")

        user = authenticate(request=self.context.get("request"), email=email, password=password)

        if not user:
            raise serializers.ValidationError({"non_field_errors": ["Invalid email or password."]})
        if not user.is_active:
            raise serializers.ValidationError({"non_field_errors": ["This account is inactive."]})

        attrs["user"] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    """Serializer for logging out and blacklisting refresh token."""
    refresh = serializers.CharField(required=True)


class TokenPairSerializer(serializers.Serializer):
    """Serializer for JWT token pair response."""
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user = UserReadSerializer(read_only=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting password reset OTP."""
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming password reset with OTP."""
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    new_password_confirm = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": ["Passwords do not match."]})

        # Validate password strength temporarily
        temp_user = User(email=attrs.get("email"))
        password_validation.validate_password(attrs["new_password"], temp_user)
        return attrs


class PasswordChangeRequestSerializer(serializers.Serializer):
    """Serializer for requesting password change OTP."""
    # We do not need fields here, just an authenticated request is enough.
    pass


class PasswordChangeConfirmSerializer(serializers.Serializer):
    """Serializer for confirming password change with OTP."""
    current_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    new_password_confirm = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})

    def validate(self, attrs):
        user = self.context["request"].user

        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError({"current_password": ["Current password is incorrect."]})

        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": ["Passwords do not match."]})

        password_validation.validate_password(attrs["new_password"], user)
        return attrs
