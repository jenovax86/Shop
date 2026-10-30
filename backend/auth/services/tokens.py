import jwt
from django.utils import timezone

from rest_framework.exceptions import AuthenticationFailed

from auth.constants import ACCESS_TOKEN_LIFETIME, REFRESH_TOKEN_LIFETIME
from shop import settings


def sign_jwt_tokens(sub: str, session_id: str) -> tuple[str, str]:
    access_token_payload = {
        'sub': str(sub),
        'sid': str(session_id),
        'exp': timezone.now() + ACCESS_TOKEN_LIFETIME,
        'iat': timezone.now(),
    }
    refresh_token_payload = {
        'sub': str(sub),
        'sid': str(session_id),
        'exp': timezone.now() + REFRESH_TOKEN_LIFETIME,
        'iat': timezone.now(),
    }
    access_token = jwt.encode(access_token_payload, settings.ACCESS_SECRET_KEY, algorithm='HS256')
    refresh_token = jwt.encode(refresh_token_payload, settings.REFRESH_SECRET_KEY, algorithm='HS256')
    return access_token, refresh_token


def decode_jwt_token(token: str, secret_key: str) -> dict:
    if not token:
        raise AuthenticationFailed("Token is missing")

    try:
        return jwt.decode(token, secret_key, algorithms=['HS256'],
                          options={"require": ["sub", "sid", "exp", "iat"]})
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationFailed(exc)
    except jwt.InvalidTokenError as exc:
        raise AuthenticationFailed(exc)


def decode_access_token(token: str) -> dict:
    return decode_jwt_token(token, settings.ACCESS_SECRET_KEY)


def decode_refresh_token(token: str) -> dict:
    return decode_jwt_token(token, settings.REFRESH_SECRET_KEY)
