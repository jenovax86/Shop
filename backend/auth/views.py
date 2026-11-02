from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView

from auth.oauth import oauth
from auth.serializers import LoginSerializer, RefreshSerializer
from auth.services.login import create_login_session, create_login_oauth_session


class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        access_token, refresh_token = create_login_session(user, request.headers.get('USER-AGENT'))
        response = Response({"success": True, "tokens": {"access": access_token}},
                            status=status.HTTP_200_OK)
        response.set_cookie(key="refresh", value=refresh_token, httponly=True)
        return response


class RefreshAPIView(TokenRefreshView):
    serializer_class = RefreshSerializer

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh')
        if not refresh_token:
            raise AuthenticationFailed("There is no refresh token.")

        serializer = self.get_serializer(data={"refresh": refresh_token})
        serializer.is_valid(raise_exception=True)
        access_token = serializer.validated_data['access']
        new_refresh_token = serializer.validated_data.get('refresh')
        response = Response({"success": True, "tokens": {"access": access_token}},
                            status=status.HTTP_200_OK)
        if new_refresh_token:
            response.set_cookie(key="refresh", value=new_refresh_token, httponly=True, secure=True, samesite="Lax")
        return response


class GoogleLogin(APIView):
    def get(self, request):
        redirect_uri = request.build_absolute_uri("/api/v1/auth/google/callback/")
        return oauth.google.authorize_redirect(request, redirect_uri)


class GoogleCallback(APIView):
    def get(self, request):
        token = oauth.google.authorize_access_token(request)
        user_info = token['userinfo']
        access_token, refresh_token = create_login_oauth_session(userinfo=user_info,
                                                                 user_agent=request.headers.get('USER-AGENT'))
        response = Response({"success": True, "tokens": {"access": access_token}},
                            status=status.HTTP_200_OK)
        response.set_cookie(key="refresh", value=refresh_token, httponly=True, secure=True, samesite="Lax")
        return response
