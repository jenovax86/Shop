from django.utils import timezone

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from auth.services.tokens import decode_access_token
from sessions.models import Session


class JwtAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', "")
        if not auth_header:
            return None

        parts = auth_header.split()
        if not parts or parts[0].lower() != "bearer":
            return None

        if len(parts) != 2:
            raise AuthenticationFailed("Invalid authorization header.")

        payload = decode_access_token(parts[1])

        session = Session.objects.select_related('user').filter(pk=payload['sid'], user=payload['sub'],
                                                                user__deleted_at__isnull=True, revoked_at__isnull=True,
                                                                expires_at__gt=timezone.now()).first()
        if session is None:
            raise AuthenticationFailed("Session expired or revoked.")

        return session.user, payload
