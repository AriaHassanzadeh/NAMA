import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,backend").split(",")
CSRF_TRUSTED_ORIGINS = os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "rest_framework", "drf_spectacular", "drf_spectacular_sidecar", "accounts", "health", "market", "workspaces",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request", "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": os.environ["POSTGRES_DB"], "USER": os.environ["POSTGRES_USER"],
    "PASSWORD": os.environ["POSTGRES_PASSWORD"],
    "HOST": os.environ.get("POSTGRES_HOST", "db"), "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    "OPTIONS": {"connect_timeout": 3},
}}
AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "URL_FORMAT_OVERRIDE": None,
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}
LANGUAGE_CODE = "fa-ir"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/api/v1/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

SPECTACULAR_SETTINGS = {
    "TITLE": "NAMA Analyze Demo API",
    "DESCRIPTION": "Labelled illustrative data, not verified market intelligence. Private workspace operations use Django sessions and CSRF.",
    "VERSION": "0.3.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "POSTPROCESSING_HOOKS": ["drf_spectacular.hooks.postprocess_schema_enums", "config.api_schema.document_csrf_header"],
    "ENUM_NAME_OVERRIDES": {
        "SourceKindEnum": "market.models.SourceKind.choices",
        "DemoSourceKindEnum": ["demo"],
        "ValueKindEnum": "market.models.ValueKind.choices",
        "PlatformEnum": "market.models.Platform.choices",
        "AdFormatEnum": "market.models.AdFormat.choices",
        "FilterAdFormatEnum": ["image", "video"],
        "CatalogKindEnum": ["ads", "products", "shops"],
        "PeriodDaysEnum": [(7, "7"), (30, "30"), (90, "90")],
        "CountryCodeEnum": ["CA", "US", "GB", "FR", "DE"],
        "CategorySlugEnum": ["fashion", "home-kitchen", "beauty-health", "lifestyle"],
        "AdOrderingEnum": ["-reach", "-roas", "-active_days", "active_days"],
        "ProductOrderingEnum": ["-growth", "price", "-active_ads", "-published_on"],
        "ShopOrderingEnum": ["-growth", "-revenue", "-visits", "-active_ads"],
    },
}
