"""
Django settings for web3 project.

Generated by 'django-admin startproject' using Django 1.10.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROJECT_ROOT = BASE_DIR


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 's-gh_-#s^oq^0*5=y8k&*^l8m9540mvo@m*tazzw%3*o7$y&m0'


ALLOWED_HOSTS = ["director.tjhsst.edu", "127.0.0.1", "localhost"]

# This is the path to the certificate that is used to authenticate with the conductor agent.
CONDUCTOR_CERT_PATH = os.path.join(PROJECT_ROOT, "settings/conductor.pem")

# Maximum number of machines that a non-staff, non-superuser account can create.
MAX_VMS = 5

# If this is set, the variable appears on all pages on Director.
GLOBAL_WARNING = None

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Default database password used in development.
DB_USERNAME = "web3"
DB_PASSWORD = "web3"

try:
    from .secret import *  # noqa
except ImportError:
    pass

if "TRAVIS" in os.environ:
    DB_USERNAME = "postgres"
    DB_PASSWORD = ""

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'social_django',
    'web3',
    'web3.apps.auth',
    'web3.apps.sites',
    'web3.apps.users',
    'web3.apps.vms',
    'web3.apps.feedback',
    'web3.apps.request'
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

ROOT_URLCONF = 'web3.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, "templates")
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
                'web3.apps.context_processors.email'
            ],
        },
    },
]

if DEBUG:
    INSTALLED_APPS += ('debug_toolbar',)
    MIDDLEWARE += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
else:
    INSTALLED_APPS += ('raven.contrib.django.raven_compat',)

WSGI_APPLICATION = 'web3.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    "default": {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'web3',
        'USER': DB_USERNAME,
        'PASSWORD': DB_PASSWORD,
        'HOST': '127.0.0.1',
        'PORT': '5432'
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, 'static/'),
)


SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'web3.apps.auth.oauth.get_username',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'web3.apps.auth.oauth.create_user_group',
    'web3.apps.auth.oauth.add_to_global_group'
)

AUTHENTICATION_BACKENDS = (
    'web3.apps.auth.oauth.IonOauth2',
    'django.contrib.auth.backends.ModelBackend',
)


AUTH_USER_MODEL = "users.User"

SOCIAL_AUTH_USER_FIELDS = ['username', 'full_name', 'email', 'id', 'is_superuser', 'is_staff']

SOCIAL_AUTH_URL_NAMESPACE = 'social'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGIN_ERROR_URL = '/login/'

INTERNAL_IPS = ['127.0.0.1']

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "mail.tjhsst.edu"
EMAIL_PORT = 25
EMAIL_USE_TLS = False  # FIXME: use tls
EMAIL_SUBJECT_PREFIX = "[Director]"
EMAIL_FROM = "director-noreply@tjhsst.edu"

EMAIL_FEEDBACK = "director@lists.tjhsst.edu"
EMAIL_CONTACT = "sysadmins@tjhsst.edu"
