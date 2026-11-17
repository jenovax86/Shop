from rest_framework import serializers
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken


class RegisterSerializer(serializers.Serializer):
    class JSONAPIMeta:
        resource_name = "users"

    username = serializers.CharField(max_length=20, required=True)
    password = serializers.CharField(max_length=100, min_length=6, required=True)


class LoginSerializer(TokenObtainPairSerializer):
    class JSONAPIMeta:
        resource_name = "tokens"


class RefreshSerializer(serializers.Serializer):
    class JSONAPIMeta:
        resource_name = "tokens"

    refresh = serializers.CharField()

    def validate_refresh(self, value):
        try:
            refresh = RefreshToken(value)
        except TokenError as exc:
            raise InvalidToken(str(exc)) from exc

        user_id = refresh.get(api_settings.USER_ID_CLAIM)
        session_id = refresh.get("sid")
        if not user_id or not isinstance(session_id, int) or isinstance(session_id, bool) or session_id < 1:
            raise InvalidToken("Invalid refresh token session.")
        return refresh
