from datetime import timedelta
from pathlib import Path
from corsheaders.defaults import default_headers
from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "rest_framework", "rest_framework_simplejwt.token_blacklist",
    "django_filters", "corsheaders",
    "core", "portfolio", "blog",
]

MIDDLEWARE = [
    "core.middleware.RequestLoggingMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

DB_ENGINE = config("DB_ENGINE", default="django.db.backends.sqlite3")
if DB_ENGINE.endswith("sqlite3"):
    DATABASES = {"default": {"ENGINE": DB_ENGINE, "NAME": BASE_DIR / config("DB_NAME", default="db.sqlite3")}}
else:
    DATABASES = {"default": {
        "ENGINE": DB_ENGINE, "NAME": config("DB_NAME"), "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"), "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Dhaka"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["core.permissions.IsOwnerOrReadOnly"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": ["core.throttles.AnonReadThrottle", "core.throttles.AnonWriteThrottle"],
    "DEFAULT_THROTTLE_RATES": {
        "anon_read": "300/min", "anon_write": "20/min",
        "comment": "5/hour", "contact": "3/hour", "like": "30/min", "login": "10/min",
    },
    "NUM_PROXIES": config("NUM_PROXIES", default=0, cast=int),
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="http://localhost:5173", cast=Csv())
CORS_ALLOW_HEADERS = list(default_headers) + ["x-visitor-id"]
CORS_EXPOSE_HEADERS = ["X-Response-Time"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "portfolio@localhost"
OWNER_NOTIFY_EMAIL = config("OWNER_NOTIFY_EMAIL", default="owner@example.com")
VIEW_COOLDOWN_SECONDS = config("VIEW_COOLDOWN_SECONDS", default=1800, cast=int)

LOGGING = {
    "version": 1, "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "[%(asctime)s] %(message)s", "datefmt": "%H:%M:%S"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "loggers": {"request": {"handlers": ["console"], "level": "INFO", "propagate": False}},
}

if not DEBUG:
    SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000


STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())