from django.contrib.auth.hashers import check_password
from rest_framework import serializers

from users.models import User


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=20, required=True)
    password = serializers.CharField(max_length=100, required=True)

    def validate(self, attrs):
        user = User.objects.filter(username=attrs['username'], deleted_at__isnull=True).first()

        if user is None or not check_password(attrs['password'], user.password):
            raise serializers.ValidationError("Invalid username or password.")

        attrs['user'] = user
        return attrs
