from django.urls import path

from auth.views import LoginAPIView, RefreshAPIView, GoogleCallback, GoogleLogin, RegisterAPIView

urlpatterns = [
    path("register/", RegisterAPIView().as_view(), name="register"),
    path("login/", LoginAPIView().as_view(), name="login"),
    path('refresh/', RefreshAPIView().as_view(), name="refresh"),
    path("google/login/", GoogleLogin().as_view(), name="google-login"),
    path("google/callback/", GoogleCallback.as_view(), name="google_callback"),
]
