from django.contrib.auth.hashers import make_password
from rest_framework_json_api import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="user-detail")
    password = serializers.CharField(max_length=100, write_only=True, trim_whitespace=False)

    class Meta:
        model = User
        fields = ["id", "url", "username", "password", "email", "first_name", "last_name"]
        read_only_fields = ["id"]

    def validate_username(self, value):
        if "@" in value:
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
            if instance.check_password(password):
                raise serializers.ValidationError("New password is identical to the old one.")

            instance.set_password(password)
        return super(UserSerializer, self).update(instance, validated_data)


class AdminUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            "role", "is_active", "is_staff", "is_superuser",
            "google_identity", "deleted_at",
        ]
