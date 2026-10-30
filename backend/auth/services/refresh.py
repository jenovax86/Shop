from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed

from auth.services.tokens import decode_refresh_token, sign_jwt_tokens
from sessions.models import Session


def refresh_session_token(refresh_token: dict):
    token = decode_refresh_token(refresh_token)

    session = Session.objects.filter(pk=token["sid"], user=token['sub'], revoked_at__isnull=True, expiers_at__gte=timezone.now()).first()
    if session is None:
        raise AuthenticationFailed("Session expired or revoked")

    access, refresh = sign_jwt_tokens(sub=str(session.user.id), session_id=str(session.pk))
    return access, refresh
