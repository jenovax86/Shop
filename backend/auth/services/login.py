from django.db import IntegrityError
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed

from auth.constants import REFRESH_TOKEN_LIFETIME
from auth.services.tokens import sign_jwt_tokens
from sessions.services.session import create_session
from users.models import User


def create_login_session(user, user_agent):
    session = create_session(user, user_agent, timezone.now() + REFRESH_TOKEN_LIFETIME)
    access_token, refresh_token = sign_jwt_tokens(user.pk, session.pk)
    return access_token, refresh_token


def create_login_oauth_session(userinfo, user_agent):
    email = userinfo.get('email')
    username = email.split('@')[0][:10]

    try:
        user, _ = User.objects.get_or_create(google_identity=userinfo['sub'], defaults={
            "username": username,
            "password": make_password(None)
        })
    except IntegrityError:
        raise AuthenticationFailed('Username already in use')

    if user.deleted_at is not None:
        raise AuthenticationFailed("Account has been deleted.")

    return create_login_session(user, user_agent)
