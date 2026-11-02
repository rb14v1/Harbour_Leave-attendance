from rest_framework import serializers

from apps.accounts.models import User


class UserBriefSerializer(serializers.ModelSerializer):
    """Minimal representation safe to nest inside other serializers."""

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "role"]
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    manager = UserBriefSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "manager",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "is_active", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    """Simple self-service registration. Not required for the demo (seed
    data covers the demo accounts) but kept for completeness - a new
    employee can sign up and optionally be assigned a manager by id."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "password",
            "role",
            "manager",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
