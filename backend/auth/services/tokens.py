from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.backends import TokenBackend

from rest_framework_simplejwt.tokens import (
    AccessToken as BaseAccessToken,
    RefreshToken as BaseRefreshToken,
)

from shop import settings
from users.models import User


def sign_jwt_tokens(user: User, session: str) -> tuple[str, str]:
    refresh = RefreshToken.for_user(user)
    refresh["sid"] = session.pk
    session.refresh_jti = refresh["jti"]
    session.save(update_fields=["refresh_jti"])
    return str(refresh.access_token), str(refresh)


class AccessToken(BaseAccessToken):
    def get_token_backend(self):
        return TokenBackend(
            algorithm="HS256",
            signing_key=settings.ACCESS_SECRET_KEY,
            verifying_key=settings.ACCESS_SECRET_KEY,
        )


class RefreshToken(BaseRefreshToken):
    access_token_class = AccessToken

    def get_token_backend(self):
        return TokenBackend(
            algorithm="HS256",
            signing_key=settings.REFRESH_SECRET_KEY,
            verifying_key=settings.REFRESH_SECRET_KEY,
        )
