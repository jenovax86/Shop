from authlib.oauth2.rfc8628 import ExpiredTokenError
from django.utils import timezone
from jwt import InvalidTokenError

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import (
    ExpiredTokenError, TokenError
)

from auth.exceptions import TokenExpired, InvalidToken
from auth.services.tokens import AccessToken
from sessions.exceptions import SessionNotFound, SessionRevoked, InvalidSessionToken
from sessions.models import Session


class SessionJWtAuthentication(JWTAuthentication):
    def get_validated_token(self, raw_token):
        try:
            return AccessToken(raw_token)
        except ExpiredTokenError:
            raise TokenExpired("Token expired exception")
        except TokenError:
            raise InvalidToken("Invalid token exception")

    def authenticate(self, request):
        result = super(SessionJWtAuthentication, self).authenticate(request)
        if result is None:
            return None

        user, token = result
        session_id = token.get("sid")
        if not session_id:
            raise InvalidSessionToken("Invalid session token exception.")

        session = Session.objects.filter(
            pk=session_id,
            user_id=user.pk,
            user__deleted_at__isnull=True,
            revoked_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).first()

        if session is None:
            raise SessionNotFound("Session expired or revoked.")

        if session.revoked_at is not None:
            raise SessionRevoked("Session revoked exception.")

        request.auth_session = session
        return user, token
