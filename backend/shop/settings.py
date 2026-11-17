import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "django-insecure-o)*zydnf9dv3o2oxd5@ubqi02m8%+)x=go(0gqjgmt969c+k&y"

DEBUG = True
ALLOWED_HOSTS = []
load_dotenv(BASE_DIR / '.env')

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

INSTALLED_APPS = [
    "rest_framework",
    "django.contrib.staticfiles",
    "core.apps.CoreConfig",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "drf_spectacular_jsonapi",
    "rest_framework_json_api",
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
    "coupons",
    "auth.apps.AuthConfig",
]

AUTH_USER_MODEL = "users.User"
SESSION_ENGINE = "django.contrib.sessions.backends.file"
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = "Lax"
ROOT_URLCONF = "shop.urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
}]

MIDDLEWARE = [
    "core.middleware.JSONAPIErrorsMiddleware",
    "core.middleware.OptionalTrailingSlashMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
]

WSGI_APPLICATION = "shop.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "HOST": os.getenv("MYSQL_HOST"),
        "USER": os.getenv("MYSQL_USER"),
        "PASSWORD": os.getenv("MYSQL_PASSWORD"),
        "NAME": os.getenv("MYSQL_DB_NAME"),
        "PORT": os.getenv("MYSQL_PORT"),
    }
}

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],

    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_SCHEMA_CLASS": "core.schema.JSONAPIAutoSchema",
    "DEFAULT_PARSER_CLASSES": ["core.parsers.JSONAPIParser"],
    "DEFAULT_CONTENT_NEGOTIATION_CLASS": "core.negotiation.JSONAPIContentNegotiation",
    "EXCEPTION_HANDLER": "core.handlers.custom_exception_handler.custom_exception_handler",
    "DEFAULT_METADATA_CLASS": "rest_framework_json_api.metadata.JSONAPIMetadata",
    "DEFAULT_PAGINATION_CLASS": "core.pagination.JSONAPIPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "rest_framework_json_api.filters.QueryParameterValidationFilter",
        "rest_framework_json_api.filters.OrderingFilter",
        "rest_framework_json_api.filters.IncludedResourcesFilter",
        "rest_framework_json_api.django_filters.DjangoFilterBackend",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "core.renderers.JSONAPIRenderer",
    ],
}

JSON_API_FORMAT_TYPES = "dasherize"
JSON_API_PLURALIZE_TYPES = True
JSON_API_UNIFORM_EXCEPTIONS = True

SIMPLE_JWT = {
    "UPDATE_LAST_LOGIN": False,
    "ACCESS_TOKEN_LIFETIME": timedelta(seconds=int(os.getenv("ACCESS_TOKEN_LIFETIME"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("REFRESH_TOKEN_LIFETIME"))),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "ALGORITHM": "HS256",

    "TOKEN_REFRESH_SERIALIZER": "auth.serializers.RefreshSerializer",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "sub",
    "ON_LOGIN_SUCCESS": "rest_framework_simplejwt.serializers.default_on_login_success",
    "ON_LOGIN_FAILED": "rest_framework_simplejwt.serializers.default_on_login_failed",

}

SPECTACULAR_SETTINGS = {
    "TITLE": "Shop API",
    "DESCRIPTION": "JSON:API shop backend. Product and category reads are public. Personal records are owner-scoped; administrators can manage all accounts and records. Role-dependent admin fields are shown in the schema and remain protected at runtime. Login returns meta.access and sets an HTTP-only refresh cookie.",
    "VERSION": "1.0.0",
    "OAS_VERSION": "3.0.3",
    "SCHEMA_PATH_PREFIX": "/api/v1",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_PUBLIC": True,
    "SERVE_AUTHENTICATION": [],
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "displayRequestDuration": True,
        "validatorUrl": None,
        "withCredentials": True,
        "persistAuthorization": False,
        "docExpansion": "none",
    },
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "refreshCookie": {"type": "apiKey", "in": "cookie", "name": "refresh",
                              "description": "HTTP-only refresh JWT set by login. Browser requests use the cookie automatically on same-origin HTTPS."},
        },
    },
}
