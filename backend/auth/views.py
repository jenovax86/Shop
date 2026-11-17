from authlib.integrations.django_client import OAuthError
from datetime import datetime, timezone as dt_timezone
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
from django.db import transaction
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from auth.oauth import oauth
from auth.serializers import RegisterSerializer, LoginSerializer, RefreshSerializer
from sessions.models import Session
from users.models import User


class RegisterAPIView(GenericAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user = User.objects.create_user(**serializer.validated_data)
            refresh = RefreshToken.for_user(user)
            expires_at = datetime.fromtimestamp(refresh["exp"], tz=dt_timezone.utc)
            session = Session.objects.create(
                user=user, user_agent=request.headers.get("User-Agent", ""),
                expires_at=expires_at, refresh_jti=refresh["jti"],
            )
            refresh["sid"] = session.pk

        location = request.build_absolute_uri(reverse("user-detail", kwargs={"pk": user.pk}))
        response = Response({
            "data": {"type": "users", "id": str(user.pk), "attributes": {"username": user.username},
                     "links": {"self": location}},
            "meta": {"access": str(refresh.access_token)},
        }, status=status.HTTP_201_CREATED)
        response["Location"] = location
        response.set_cookie(
            key="refresh",
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite="Lax",
            expires=expires_at,
        )
        return response


class LoginAPIView(TokenObtainPairView):
    serializer_class = LoginSerializer

    def __init__(self):
        self.login_serializer = None

    def get_serializer(self, *args, **kwargs):
        self.login_serializer = super().get_serializer(*args, **kwargs)
        return self.login_serializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        user = self.login_serializer.user

        refresh = RefreshToken(response.data["refresh"])
        with transaction.atomic():
            user_agent = request.headers.get("User-Agent", "")
            expires_at = datetime.fromtimestamp(refresh["exp"], tz=dt_timezone.utc)
            session = Session.objects.create(
                user=user,
                user_agent=user_agent,
                expires_at=expires_at,
                refresh_jti=refresh["jti"],
            )
            refresh["sid"] = session.pk

        response.data = {"meta": {"access": str(refresh.access_token)}}
        response.set_cookie(key="refresh", value=str(refresh), httponly=True, secure=True, samesite="Lax",
                            expires=expires_at)
        return response


class RefreshAPIView(TokenRefreshView):
    serializer_class = RefreshSerializer

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh")
        serializer = self.get_serializer(data={"refresh": refresh_token})
        serializer.is_valid(raise_exception=True)

        refresh = serializer.validated_data["refresh"]

        with transaction.atomic():
            session = Session.objects.select_for_update().filter(
                pk=refresh["sid"],
                user_id=refresh[api_settings.USER_ID_CLAIM],
                refresh_jti=refresh["jti"],
                user__deleted_at__isnull=True,
                user__is_active=True,
                revoked_at__isnull=True,
                expires_at__gt=timezone.now(),
            ).first()
            if session is None:
                raise AuthenticationFailed("Session expired or revoked.")

            self.rotate_refresh(refresh)
            session.refresh_jti = refresh["jti"]
            session.expires_at = datetime.fromtimestamp(refresh["exp"], tz=dt_timezone.utc)
            session.save(update_fields=["refresh_jti", "expires_at"])

        response = Response({"meta": {"access": str(refresh.access_token)}},
                            status=status.HTTP_200_OK)
        response.set_cookie(
            key="refresh", value=str(refresh), httponly=True, secure=True,
            samesite="Lax", expires=session.expires_at,
        )
        return response

    @staticmethod
    def rotate_refresh(refresh: RefreshToken):
        refresh.set_jti()
        refresh.set_exp()
        refresh.set_iat()


class GoogleLogin(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        redirect_uri = request.build_absolute_uri("/api/v1/auth/google/callback/")
        return oauth.google.authorize_redirect(request, redirect_uri)


class GoogleCallback(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            token = oauth.google.authorize_access_token(request)
        except OAuthError as exc:
            raise ValidationError("Google authorization failed.") from exc

        user_info = token.get("userinfo") or {}
        google_identity = user_info.get("sub")
        email = user_info.get("email")
        user_agent = request.headers.get("User-Agent", "")
        if not google_identity or not email:
            raise ValidationError("Google did not return the required account information.")

        try:
            with transaction.atomic():
                user, _ = User.objects.get_or_create(
                    google_identity=google_identity,
                    defaults={
                        "username": email.split("@", 1)[0][:10],
                        "password": make_password(None),
                    },
                )
                if user.deleted_at is not None or not user.is_active:
                    raise PermissionDenied("Account is deleted or disabled.")

                refresh = RefreshToken.for_user(user)
                expires_at = datetime.fromtimestamp(refresh["exp"], tz=dt_timezone.utc)
                session = Session.objects.create(
                    user=user,
                    user_agent=user_agent,
                    expires_at=expires_at,
                    refresh_jti=refresh["jti"],
                )
                refresh["sid"] = session.pk
        except IntegrityError as exc:
            raise ValidationError("Unable to create Google login account: username already in use.") from exc

        response = Response(
            {"meta": {"access": str(refresh.access_token)}},
            status=status.HTTP_200_OK,
        )
        response.set_cookie(
            key="refresh", value=str(refresh), httponly=True, secure=True,
            samesite="Lax", expires=expires_at,
        )
        return response
