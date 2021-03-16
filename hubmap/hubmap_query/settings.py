"""
Django settings for hubmap_query project.

Generated by 'django-admin startproject' using Django 3.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""
import sys
from datetime import timedelta
from os import fspath
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# !!! for development, overridden in `production_settings.py` by Docker container build

SECRET_KEY = "w!%f(4op=)1ivs#g@pwj5%035tvw9!tg^svrhtddjuh#sbp!+@"

DEBUG = True

ALLOWED_HOSTS = ["*"]

# /!!! for development, overridden in `production_settings.py` by Docker container build

CELERY_BROKER_URL = "redis://redis:6379"
CELERY_TIMEZONE = "America/New_York"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60

QUERY_TOKEN_EXPIRATION = timedelta(days=1)

# database is local to each web app instance, not worth overriding
# credentials for production deployment at the moment
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "postgres",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "db",
        "PORT": 5432,
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyLibMCCache",
        # same in development and current production configuration; will
        # likely need to override for deployment by IEC
        "LOCATION": "memcached:11211",
    }
}

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "query_app",
    "rest_framework",
    "bootstrap4",
    "django_tables2",
    "corsheaders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "hubmap_query.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "hubmap_query.wsgi.application"

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

CORS_ALLOW_ALL_ORIGINS = True

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

ALLOWED_IPS = []

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = "/static/"

# Keep this as the last section of this file!
try:
    from .local_settings import *
except ImportError:
    pass
# Intended to be a temporary hack for overriding settings in production.
# TODO: figure out a better way to do this, probably with a different path
override_settings_file = Path("/opt/secret/override_settings.py")
if override_settings_file.is_file():
    print("Reading production override settings from", override_settings_file)
    sys.path.append(fspath(override_settings_file.parent))
    try:
        from override_settings import *
    except ImportError as e:
        print("Couldn't read override settings found at", override_settings_file)
        raise
# Sometimes we do need to define settings in terms of other settings, so
# this is a good place to do so, after override settings are loaded.
# Shouldn't define any constants at this point though

# !!! overrides that depend on other (including local) settings

#  (none yet)

# /!!! overrides that depend on other (including local) settings

# Do not add anything after this
