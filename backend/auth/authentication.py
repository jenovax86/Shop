from django.utils import timezone

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from auth.services.tokens import decode_access_token
from sessions.models import Session


class JwtAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = request.headers.get('Authorization')
        parts = token.split()
        if not token or parts[0].lower() != "bearer":
            return None

        payload = decode_access_token(parts[1])

        session = Session.objects.select_related('user').filter(pk=payload['sid'], user=payload['sub'], revoked_at__isnull=True,
                                         expires_at__gt=timezone.now()).first()
        if session is None:
            raise AuthenticationFailed("Session expired or revoked.")

        return session.user, payload
