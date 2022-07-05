"""
Django settings for StudentiUniMi project.

Generated by 'django-admin startproject' using Django 3.2.5.
"""

from pathlib import Path
import os
import sys
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", False)
if not SECRET_KEY or len(SECRET_KEY) == 0:
    print("+++[SECURITY ALERT]+++\tYou didn't set the SECRET_KEY env variable. *DO NOT* run this thing in production!")
    SECRET_KEY = "abc"


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(os.environ.get("DEBUG", False))

ALLOWED_HOSTS = [
    'django',
    '127.0.0.1',
]

INSTALLED_APPS = [
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'background_task',
    'polymorphic',
    'university',
    'telegrambot',
    'roles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'StudentiUniMi.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'StudentiUniMi.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': 'postgres',
        'PORT': 5432,
        'NAME': os.environ.get("POSTGRES_DBNAME"),
        'USER': os.environ.get("POSTGRES_USER"),
        'PASSWORD': os.environ.get("POSTGRES_PASSWORD"),
    }
}
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'TEST_CHARSET': 'UTF8',
        'NAME': ':memory:',
        'TEST_NAME': ':memory:',
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Rome'
USE_I18N = True
USE_L10N = True
USE_TZ = False
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

LANGUAGES = [
    ('en', 'English'),
    ('it', 'Italian'),
]
MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

DEFAULT_RENDER_CLASSES = (
    'rest_framework.renderers.JSONRenderer',
)
if DEBUG:
    DEFAULT_RENDER_CLASSES += (
        'rest_framework.renderers.BrowsableAPIRenderer',
    )

REAL_HOST = 'https://api-staging.studentiunimi.it' if DEBUG else 'https://api.studentiunimi.it'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_RENDERER_CLASSES': DEFAULT_RENDER_CLASSES,
}

LOGGING_CHAT_ID = os.environ.get("LOGGING_CHAT_ID", 0)
LOGGING_BOT_TOKEN = os.environ.get("LOGGING_BOT_TOKEN", "")

TELEGRAM_API_ID = os.environ.get("TELEGRAM_API_ID", None)
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH", None)

TELEGRAM_ADMIN_GROUP_ID = os.environ.get("TELEGRAM_ADMIN_GROUP_ID", 0)

GROUPHELP_BLOCKLIST_URL = os.environ.get("GROUPHELP_BLOCKLIST_URL", None)

if not DEBUG and len(os.environ.get("SENTRY_DSN", '')) > 0:
    with open("version.txt", "r+") as f:
        sentry_sdk.init(
            dsn=os.environ["SENTRY_DSN"],
            integrations=[DjangoIntegration()],
            release=f.read().strip(),
            server_name=os.environ.get("SERVER_NAME", None),
            traces_sample_rate=1.0,
            send_default_pii=True,
        )
