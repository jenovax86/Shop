from rest_framework import serializers

from sessions.models import Session


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['id', 'revoked_at', 'created_at', 'expires_at', 'user_agent']
        read_only_fields = ['revoked_at', 'created_at', 'expires_at', 'user_agent']


class RevokeSessionSerializer(serializers.Serializer):
    session_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        max_length=100
    )
