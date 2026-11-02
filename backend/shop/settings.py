import os
from datetime import timedelta
from pathlib import Path

from django.conf.global_settings import AUTH_USER_MODEL
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "django-insecure-o)*zydnf9dv3o2oxd5@ubqi02m8%+)x=go(0gqjgmt969c+k&y"

DEBUG = True

ALLOWED_HOSTS = []
load_dotenv(BASE_DIR / '.env')

ACCESS_SECRET_KEY = os.environ.get('JWT_ACCESS_TOKEN_SECRET')
REFRESH_SECRET_KEY = os.environ.get('JWT_REFRESH_TOKEN_SECRET')
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
ACCESS_TOKEN_LIFETIME = timedelta(minutes=10)
REFRESH_TOKEN_LIFETIME = timedelta(days=1)

INSTALLED_APPS = [
    "rest_framework",
    "django_filters",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "users",
    "categories",
    "products",
    "addresses",
    "orders",
    "carts",
    "sessions",
    "auth.apps.AuthConfig",
]

AUTH_USER_MODEL = "users.User"
SESSION_ENGINE = "django.contrib.sessions.backends.file"
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = "Lax"
ROOT_URLCONF = "shop.urls"

TEMPLATES = []

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
]

WSGI_APPLICATION = "shop.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "HOST": os.getenv("SHOP_HOST"),
        "USER": os.getenv("SHOP_USER"),
        "PASSWORD": os.getenv("SHOP_PASSWORD"),
        "NAME": os.getenv("SHOP_NAME"),
        "PORT": os.getenv("SHOP_PORT"),
    }
}

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],

    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "UNAUTHENTICATED_USER": None,
}

SIMPLE_JWT = {
    "UPDATE_LAST_LOGIN": False,
    "ACCESS_TOKEN_LIFETIME": ACCESS_TOKEN_LIFETIME,
    "REFRESH_TOKEN_LIFETIME": REFRESH_TOKEN_LIFETIME,
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",

    "AUTH_TOKEN_CLASSES": [
        "auth.services.tokens.AccessToken",
    ],
    "TOKEN_REFRESH_SERIALIZER": [
      "auth.serializers.RefreshSerializer",
    ],
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "sub",
    "ON_LOGIN_SUCCESS": "rest_framework_simplejwt.serializers.default_on_login_success",
    "ON_LOGIN_FAILED": "rest_framework_simplejwt.serializers.default_on_login_failed",
    "JTI_CLAIM": "jti",

}
