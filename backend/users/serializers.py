from django.contrib.auth.hashers import make_password, check_password
from rest_framework import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=100, write_only=True)

    class Meta:
        model = User
        fields = ["username", "password", ]

    def validate_username(self, value):
        if "@"in value:
            raise serializers.ValidationError("Username cannot be email")
        return value

    def validate_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data["password"] = make_password(password)
        return super(UserSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        if password is not None:
            if check_password(password, instance.password):
                raise serializers.ValidationError("New password is identical to the old one.")

            instance.password = make_password(password)
        return super(UserSerializer, self).update(instance, validated_data)
