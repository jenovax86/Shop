from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from auth.services.tokens import RefreshToken
from sessions.models import Session


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=20, required=True)
    password = serializers.CharField(max_length=100, required=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])

        if user is None:
            raise serializers.ValidationError("Invalid username or password.")

        attrs['user'] = user
        return attrs


class RefreshSerializer(TokenRefreshSerializer):
    token_class = RefreshToken

    def validate(self, attrs):
        refresh = self.token_class(attrs["refresh"])
        user_id = refresh.payload.get(api_settings.USER_ID_CLAIM)
        session_id = refresh.payload.get("sid")

        if not user_id or not session_id:
            raise AuthenticationFailed("Invalid refresh token.")

        session = Session.objects.filter(pk=session_id, user=user_id, refresh_jti=refresh["jti"],
                                         user__deleted_at__isnull=True,
                                         revoked_at__isnull=True,
                                         expires_at__gte=timezone.now()).first()
        if session is None:
            raise AuthenticationFailed("Session expired or revoked")

        data = super(RefreshSerializer, self).validate(attrs)
        if "refresh" in data:
            new_refresh = self.token_class(data["refresh"])
            session.refresh = new_refresh['jti']
            session.save(update_fields=["refresh_jti"])

        return data
