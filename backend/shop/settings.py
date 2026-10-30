import os
from pathlib import Path

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

INSTALLED_APPS = [
    "rest_framework",
    "django_filters",
    "django.contrib.contenttypes",
    "users",
    "categories",
    "products",
    "addresses",
    "orders",
    "carts",
    "sessions",
    "auth",
]


SESSION_ENGINE = "django.contrib.sessions.backends.file"
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = "Lax"
ROOT_URLCONF = "shop.urls"

TEMPLATES = []

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
    # "EXCEPTION_HANDLER": "core.exception_handler.custom_exception_handler",
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}
