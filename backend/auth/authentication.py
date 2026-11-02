from django.utils import timezone

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

from sessions.models import Session


class SessionJWtAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super(SessionJWtAuthentication, self).authenticate(request)
        print(result)
        if result is None:
            return None

        user, token = result
        session_id = token.get("sid")
        if not session_id:
            raise AuthenticationFailed("There is no session id.")

        session = Session.objects.filter(
            pk=session_id,
            user_id=user.pk,
            user__deleted_at__isnull=True,
            revoked_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).first()

        if session is None:
            raise AuthenticationFailed(
                "Session expired or revoked."
            )

        request.auth_session = session
        return user, token

